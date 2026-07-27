// GET /api/china-universities
// Uses Postgres RPC to avoid Supabase 1000-row anon limit on china_programs (11,472 rows)
// Public data — uses anon key (RLS: public SELECT)

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://ufspivvuevllmkxmivbe.supabase.co';
const SUPABASE_KEY = process.env.SUPABASE_ANON_KEY || 'sb_publishable_5iAEih-Cq-6cIAihBLuSVQ_lKYf8a0x';

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
    const { city, language, degree_level, max_tuition_usd, tier, sort_by } = params;

    // Step 1: Call RPC — does full aggregation + filtering in one Postgres query
    // This avoids the Supabase 1000-row anon limit on china_programs (11,472 rows)
    const rpcParams = {
      p_city: city && city !== 'All' ? city : null,
      p_language: language && language !== 'All' ? language : null,
      p_degree_level: degree_level && degree_level !== 'All' ? degree_level : null,
      p_max_tuition_usd: max_tuition_usd ? parseFloat(max_tuition_usd) : null,
      p_tier: tier && tier !== 'All' ? tier : null,
    };

    const { data: universities, error } = await supabase.rpc('get_china_universities', rpcParams);
    if (error) throw error;
    if (!universities || universities.length === 0) {
      return { statusCode: 200, headers: HEADERS, body: JSON.stringify({ universities: [], total: 0 }) };
    }

    const total = universities.length;

    // Step 2: Sort
    if (sort_by === 'programs') {
      universities.sort((a, b) => b.program_count - a.program_count);
    } else {
      // Default: QS ranked universities first (ascending rank), then unranked by program count
      universities.sort((a, b) => {
        if (a.qs_rank && b.qs_rank) return a.qs_rank - b.qs_rank;
        if (a.qs_rank) return -1;
        if (b.qs_rank) return 1;
        return b.program_count - a.program_count;
      });
    }

    const topResults = universities.slice(0, 100);

    // Step 3: Fetch subject strengths for displayed universities (top-10 world rankings only)
    const displayedIds = topResults.map(u => u.id);
    const { data: subjects } = await supabase
      .from('university_subjects')
      .select('university_id, subject, subject_rank')
      .in('university_id', displayedIds)
      .lte('subject_rank', 10)
      .order('subject_rank', { ascending: true });

    // Group by university_id — keep top 3 per uni
    const subjectMap = {};
    if (subjects) {
      for (const s of subjects) {
        if (!subjectMap[s.university_id]) subjectMap[s.university_id] = [];
        if (subjectMap[s.university_id].length < 3) {
          subjectMap[s.university_id].push({ subject: s.subject, rank: s.subject_rank });
        }
      }
    }

    // Step 4: Attach subjects and normalise types
    const result = topResults.map(u => ({
      id: u.id,
      name_en: u.name_en,
      city: u.city,
      province: u.province,
      is_985: u.is_985,
      is_211: u.is_211,
      qs_rank: u.qs_rank,
      qs_score: u.qs_score ? parseFloat(u.qs_score) : null,
      program_count: parseInt(u.program_count, 10) || 0,
      min_tuition_usd: u.min_tuition_usd ? parseFloat(u.min_tuition_usd) : null,
      languages: u.languages || [],
      top_subjects: subjectMap[u.id] || [],
    }));

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
