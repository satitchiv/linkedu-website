// GET /api/china-universities
// Filterable university list with program stats
// Public data — uses anon key (RLS: public SELECT)

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://ufspivvuevllmkxmivbe.supabase.co';
const SUPABASE_KEY = process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmc3BpdnZ1ZXZsbG1reG1pdmJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxMTU2MDUsImV4cCI6MjA4ODY5MTYwNX0.aybHZVeG4_gl5RDXjrhfTAKNq0sUEdYslwuwTdghIpk';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

const HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json',
};

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers: HEADERS, body: '' };
  }

  try {
    const params = event.queryStringParameters || {};
    const { city, language, degree_level, max_tuition_usd } = params;

    // Step 1: If city filter, resolve university IDs for that city
    let cityUniversityIds = null;
    if (city && city !== 'All') {
      const { data: unis, error: cityErr } = await supabase
        .from('china_universities')
        .select('id')
        .eq('city', city);

      if (cityErr) throw cityErr;
      cityUniversityIds = unis ? unis.map(u => u.id) : [];

      if (cityUniversityIds.length === 0) {
        return {
          statusCode: 200,
          headers: HEADERS,
          body: JSON.stringify({ universities: [], total: 0 }),
        };
      }
    }

    // Step 2: Query programs with filters (high range to get all matching rows)
    let programQuery = supabase
      .from('china_programs')
      .select('university_id, language, degree_level, tuition_usd_per_year')
      .range(0, 11999);

    if (language && language !== 'All') {
      programQuery = programQuery.ilike('language', `%${language}%`);
    }
    if (degree_level && degree_level !== 'All') {
      programQuery = programQuery.eq('degree_level', degree_level);
    }
    if (max_tuition_usd) {
      programQuery = programQuery.lte('tuition_usd_per_year', parseFloat(max_tuition_usd));
    }
    if (cityUniversityIds) {
      programQuery = programQuery.in('university_id', cityUniversityIds);
    }

    const { data: programs, error: progErr } = await programQuery;
    if (progErr) throw progErr;

    if (!programs || programs.length === 0) {
      return {
        statusCode: 200,
        headers: HEADERS,
        body: JSON.stringify({ universities: [], total: 0 }),
      };
    }

    // Step 3: Aggregate by university_id in JS
    const uniMap = {};
    for (const p of programs) {
      if (!p.university_id) continue;
      if (!uniMap[p.university_id]) {
        uniMap[p.university_id] = {
          program_count: 0,
          min_tuition_usd: null,
          languages: new Set(),
          degree_levels: new Set(),
        };
      }
      const u = uniMap[p.university_id];
      u.program_count++;
      if (p.tuition_usd_per_year != null) {
        if (u.min_tuition_usd === null || p.tuition_usd_per_year < u.min_tuition_usd) {
          u.min_tuition_usd = p.tuition_usd_per_year;
        }
      }
      if (p.language) u.languages.add(p.language);
      if (p.degree_level) u.degree_levels.add(p.degree_level);
    }

    const uniIds = Object.keys(uniMap);
    const total = uniIds.length;

    // Sort by program_count descending, take top 100
    const topIds = uniIds
      .sort((a, b) => uniMap[b].program_count - uniMap[a].program_count)
      .slice(0, 100);

    // Step 4: Fetch university details for top 100
    const { data: universities, error: uniErr } = await supabase
      .from('china_universities')
      .select('id, source_id, name_en, city, province')
      .in('id', topIds);

    if (uniErr) throw uniErr;
    if (!universities) {
      return {
        statusCode: 200,
        headers: HEADERS,
        body: JSON.stringify({ universities: [], total: 0 }),
      };
    }

    // Step 5: Merge university details with aggregated program stats
    const result = universities
      .map(u => ({
        id: u.id,
        source_id: u.source_id,
        name_en: u.name_en,
        city: u.city,
        province: u.province,
        program_count: uniMap[u.id]?.program_count || 0,
        min_tuition_usd: uniMap[u.id]?.min_tuition_usd,
        languages: [...(uniMap[u.id]?.languages || [])],
        degree_levels: [...(uniMap[u.id]?.degree_levels || [])],
      }))
      .sort((a, b) => b.program_count - a.program_count);

    return {
      statusCode: 200,
      headers: HEADERS,
      body: JSON.stringify({ universities: result, total }),
    };
  } catch (err) {
    console.error('[china-universities]', err);
    return {
      statusCode: 500,
      headers: HEADERS,
      body: JSON.stringify({ error: err.message }),
    };
  }
};
