-- Threads table: lightweight index of per-user conversations.
-- Checkpoint data is stored separately by LangGraph's PostgresSaver.
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor > New query).

CREATE TABLE IF NOT EXISTS threads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    thread_id TEXT UNIQUE NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE threads ENABLE ROW LEVEL SECURITY;

-- Users can read their own threads
CREATE POLICY "Users can select own threads"
    ON threads FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own threads
CREATE POLICY "Users can insert own threads"
    ON threads FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own threads
CREATE POLICY "Users can delete own threads"
    ON threads FOR DELETE
    USING (auth.uid() = user_id);

-- Service role bypasses RLS, so server-side inserts via supabase_admin work automatically.
