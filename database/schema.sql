-- YourCast Database Schema for Supabase
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (optional for MVP, but good for future)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Episodes table
CREATE TABLE episodes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    duration_seconds INTEGER DEFAULT 0,
    subcategories JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    audio_url TEXT,
    transcript_url TEXT,
    vtt_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sources table (stores news articles)
CREATE TABLE sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    published_date TIMESTAMP WITH TIME ZONE,
    excerpt TEXT,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Episode segments table (for chapter navigation)
CREATE TABLE episode_segments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE NOT NULL,
    start_time INTEGER NOT NULL, -- seconds from start
    end_time INTEGER NOT NULL,   -- seconds from start
    text TEXT NOT NULL,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_episodes_status ON episodes(status);
CREATE INDEX idx_episodes_created_at ON episodes(created_at);
CREATE INDEX idx_episodes_user_id ON episodes(user_id);
CREATE INDEX idx_sources_episode_id ON sources(episode_id);
CREATE INDEX idx_episode_segments_episode_id ON episode_segments(episode_id);
CREATE INDEX idx_episode_segments_order ON episode_segments(episode_id, order_index);

-- Update updated_at trigger for episodes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_episodes_updated_at BEFORE UPDATE ON episodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) policies - optional for MVP
-- Uncomment if you want to enable user-specific data access

-- ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE episode_segments ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can view their own episodes" ON episodes
--     FOR SELECT USING (auth.uid() = user_id);

-- CREATE POLICY "Users can create their own episodes" ON episodes
--     FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Storage bucket setup (run this via Supabase dashboard or storage API)
-- Create a bucket called 'podcasts' with public read access

-- Sample data for testing
INSERT INTO episodes (id, title, description, subcategories, status) VALUES
(
    uuid_generate_v4(),
    'Tech News Update - AI Developments',
    'Latest developments in artificial intelligence and technology',
    '["technology", "artificial intelligence"]',
    'completed'
);

COMMENT ON TABLE episodes IS 'Stores podcast episode metadata and status';
COMMENT ON TABLE sources IS 'News articles used to generate podcast episodes';
COMMENT ON TABLE episode_segments IS 'Timestamped segments for chapter navigation';
COMMENT ON COLUMN episodes.subcategories IS 'JSON array of subcategory strings';
COMMENT ON COLUMN episodes.status IS 'Current generation status of the episode';