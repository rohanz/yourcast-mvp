import logging
import hashlib
import uuid
import json
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from agent.config import settings
from agent.services.embedding_service import EmbeddingService
from agent.services.llm_service import LLMService
from agent.rss_config import get_feed_category, get_category_subcategories

# Import models (we'll need to update the import path based on your structure)
# from app.models.article import Article
# from app.models.story_cluster import StoryCluster

logger = logging.getLogger(__name__)

class ClusteringService:
    def __init__(self, db_session: Session, debug_llm_responses: bool = False):
        """Initialize the clustering service"""
        self.db = db_session
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.similarity_threshold = 0.85
        self.debug_llm_responses = debug_llm_responses
        
    def process_article(self, article_data: Dict[str, Any]) -> Optional[str]:
        """
        Process a single article through the clustering pipeline
        
        Args:
            article_data: Dictionary containing article metadata
            
        Returns:
            Article ID if successful, None if failed or duplicate
        """
        try:
            # Step 1: Calculate uniqueness hash
            uniqueness_hash = self._calculate_hash(article_data['url'])
            
            # Step 2: Check for duplicates
            if self._is_duplicate(uniqueness_hash):
                logger.info(f"Skipping duplicate article: {article_data['title']}")
                return None
            
            # Step 3: Generate embedding
            embedding_text = f"{article_data['title']} {article_data.get('summary', '')}"
            embedding = self.embedding_service.generate_embedding(embedding_text)
            
            if embedding is None:
                logger.error(f"Failed to generate embedding for: {article_data['title']}")
                return None
            
            # Step 4: Find similar articles and clusters
            similar_articles, cluster_candidates = self._find_similar_articles(embedding)
            
            # Step 5: Use AI judge to determine clustering
            cluster_decision = self._ai_judge_clustering(article_data, similar_articles)
            
            # Step 6: Process clustering decision
            if cluster_decision['action'] == 'create_new':
                cluster_id = self._create_new_cluster(article_data, cluster_decision)
            else:
                cluster_id = cluster_decision['cluster_id']
            
            # Step 7: Save article to database
            article_id = self._save_article(
                article_data, 
                uniqueness_hash, 
                embedding, 
                cluster_id,
                cluster_decision
            )
            
            logger.info(f"Successfully processed article: {article_data['title']} -> {cluster_id}")
            return article_id
            
        except Exception as e:
            logger.error(f"Failed to process article {article_data.get('title', 'Unknown')}: {str(e)}")
            # Rollback any failed transaction to reset connection state
            try:
                self.db.rollback()
            except:
                pass
            return None
    
    def process_articles_batch(self, articles_data: List[Dict[str, Any]]) -> List[Optional[str]]:
        """Process multiple articles in a batch"""
        results = []
        for article_data in articles_data:
            result = self.process_article(article_data)
            results.append(result)
        return results
    
    def _calculate_hash(self, url: str) -> str:
        """Calculate MD5 hash of URL for duplicate detection"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _is_duplicate(self, uniqueness_hash: str) -> bool:
        """Check if article hash already exists in database"""
        # TODO: Replace with actual database query
        # query = self.db.query(Article).filter(Article.uniqueness_hash == uniqueness_hash).first()
        # return query is not None
        
        # Placeholder implementation
        result = self.db.execute(
            text("SELECT 1 FROM articles WHERE uniqueness_hash = :hash LIMIT 1"),
            {"hash": uniqueness_hash}
        ).fetchone()
        return result is not None
    
    def _find_similar_articles(self, embedding: np.ndarray) -> Tuple[List[Dict], List[str]]:
        """
        Find articles with similar embeddings using pgvector
        
        Returns:
            Tuple of (similar_articles_data, cluster_ids)
        """
        try:
            # Convert numpy array to list for SQL
            embedding_list = embedding.tolist()
            
            # Use pgvector's cosine similarity search
            # This query finds articles with similarity > threshold
            # Use CAST syntax instead of ::vector with bind parameters
            query = text("""
                SELECT 
                    article_id, title, summary, cluster_id, source_name,
                    1 - (embedding <=> CAST(:embedding_param AS vector)) as similarity
                FROM articles 
                WHERE 1 - (embedding <=> CAST(:embedding_param AS vector)) > :threshold_param
                ORDER BY similarity DESC
                LIMIT 10
            """)
            
            results = self.db.execute(query, {
                "embedding_param": json.dumps(embedding_list),
                "threshold_param": self.similarity_threshold
            }).fetchall()
            
            similar_articles = []
            cluster_candidates = set()
            
            for row in results:
                similar_articles.append({
                    'article_id': row.article_id,
                    'title': row.title,
                    'summary': row.summary,
                    'cluster_id': row.cluster_id,
                    'source_name': row.source_name,
                    'similarity': row.similarity
                })
                cluster_candidates.add(row.cluster_id)
            
            return similar_articles, list(cluster_candidates)
            
        except Exception as e:
            logger.error(f"Failed to find similar articles: {str(e)}")
            try:
                self.db.rollback()
            except:
                pass
            return [], []
    
    def _ai_judge_clustering(self, new_article: Dict[str, Any], similar_articles: List[Dict]) -> Dict[str, Any]:
        """
        Use AI to determine if article should join existing cluster or create new one
        """
        # Use feed category if available, otherwise fall back to keyword categorization
        feed_category = new_article.get('feed_category', self._categorize_article(new_article))
        
        if not similar_articles:
            # Still call AI judge to generate subcategories and tags, even without similar articles
            try:
                # Use the existing clustering prompt but with empty similar_articles list
                prompt = self._create_clustering_prompt(new_article, [])
                response = self.llm_service.generate_text(prompt)
                
                # Debug: Log the LLM response if enabled
                if self.debug_llm_responses:
                    print(f"\n🤖 LLM Response for '{new_article['title'][:50]}...':")
                    print(f"📝 Response: {response}")
                    print("-" * 80)
                
                decision = self._parse_ai_decision(response, [])
                
                # Ensure it's marked as create_new
                decision['action'] = 'create_new'
                decision['reason'] = 'No similar articles found'
                decision['cluster_id'] = None
                
                return decision
                
            except Exception as e:
                logger.error(f"AI categorization failed: {str(e)}")
                return {
                    'action': 'create_new',
                    'reason': 'No similar articles found, AI categorization failed',
                    'category': feed_category,
                    'subcategory': None,
                    'tags': []
                }
        
        try:
            # Prepare context for AI judge
            similar_context = []
            for article in similar_articles[:5]:  # Limit to top 5 most similar
                similar_context.append({
                    'title': article['title'],
                    'summary': article['summary'],
                    'cluster_id': article['cluster_id'],
                    'similarity': article['similarity']
                })
            
            # Create prompt for AI judge
            prompt = self._create_clustering_prompt(new_article, similar_context)
            
            # Get AI decision
            response = self.llm_service.generate_text(prompt)
            
            # Debug: Log the LLM response if enabled
            if self.debug_llm_responses:
                print(f"\n🤖 LLM Response for '{new_article['title'][:50]}...':")
                print(f"📝 Response: {response}")
                print("-" * 80)
            
            decision = self._parse_ai_decision(response, similar_articles)
            
            return decision
            
        except Exception as e:
            logger.error(f"AI judge failed, creating new cluster: {str(e)}")
            return {
                'action': 'create_new',
                'reason': 'AI judge error',
                'category': self._categorize_article(new_article),
                'subcategory': None,
                'tags': []
            }
    
    def _create_clustering_prompt(self, new_article: Dict[str, Any], similar_articles: List[Dict]) -> str:
        """Create prompt for AI clustering decision"""
        
        # Get feed category and available subcategories
        feed_category = new_article.get('feed_category', self._categorize_article(new_article))
        available_subcategories = get_category_subcategories(feed_category)
        
        prompt = f"""You are a news editor determining if articles belong to the same story.

NEW ARTICLE:
Title: {new_article['title']}
Summary: {new_article.get('summary', 'No summary')}
Source: {new_article['source_name']}
Feed Category: {feed_category}

SIMILAR EXISTING ARTICLES:
"""
        
        for i, article in enumerate(similar_articles, 1):
            prompt += f"""
{i}. Title: {article['title']}
   Summary: {article['summary']}
   Cluster ID: {article['cluster_id']}
   Similarity: {article['similarity']:.3f}
"""
        
        # Add available subcategories to the prompt
        subcategories_str = ', '.join(available_subcategories) if available_subcategories else "None defined"
        
        # Add few-shot examples based on category
        examples = self._get_few_shot_examples(feed_category)
        
        prompt += f"""
INSTRUCTIONS:
1. Determine if the new article is about the same story as any existing article
2. Consider: same event, same people/companies, same timeframe, same core topic
3. Don't cluster if articles are just in the same category but about different events
4. The article is from a {feed_category} feed, so assign an appropriate subcategory from: {subcategories_str}
5. Generate 2-4 relevant tags that capture key entities, topics, or themes

EXAMPLES:
{examples}

Respond with JSON only:
{{
    "action": "join_existing" or "create_new",
    "cluster_id": "cluster_id_to_join" or null,
    "reason": "brief explanation",
    "category": "{feed_category}",
    "subcategory": "choose from: {subcategories_str}", 
    "tags": ["tag1", "tag2", "tag3"]
}}"""
        
        return prompt
    
    def _get_few_shot_examples(self, category: str) -> str:
        """Get few-shot examples based on category"""
        examples = {
            "Technology": """
Example 1 - CREATE NEW CLUSTER:
Article: "Apple Announces New MacBook Pro with M3 Chip"
Summary: "Apple unveiled its latest MacBook Pro featuring the new M3 processor with improved performance and battery life"
Similar Articles: None found
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "New product announcement, no similar stories found",
    "category": "Technology",
    "subcategory": "Gadgets & Consumer Tech",
    "tags": ["Apple", "MacBook Pro", "M3 chip", "product launch"]
}

Example 2 - JOIN EXISTING CLUSTER:
Article: "M3 MacBook Pro Shows 20% Performance Boost in Benchmarks"
Summary: "Early benchmark tests reveal significant performance improvements in the new M3-powered MacBook Pro"
Similar Articles: "Apple Announces New MacBook Pro with M3 Chip" (similarity: 0.89)
Decision:
{
    "action": "join_existing",
    "cluster_id": "tech-123-abc",
    "reason": "Same product launch story, just benchmark details",
    "category": "Technology",
    "subcategory": "Gadgets & Consumer Tech",
    "tags": ["Apple", "MacBook Pro", "M3 chip", "benchmarks", "performance"]
}

Example 3 - CREATE NEW (Different story):
Article: "Google Releases Gemini 2.0 AI Model"
Summary: "Google announced Gemini 2.0, its most advanced AI model with multimodal capabilities"
Similar Articles: "Apple Announces New MacBook Pro with M3 Chip" (similarity: 0.72)
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "Different company, different product category (AI vs hardware)",
    "category": "Technology",
    "subcategory": "AI & Machine Learning",
    "tags": ["Google", "Gemini", "AI model", "multimodal", "machine learning"]
}""",

            "Sports": """
Example 1 - CREATE NEW CLUSTER:
Article: "Tiger Woods Wins Masters Tournament by 2 Strokes"
Summary: "Tiger Woods captured his sixth Masters title with a final round 68 at Augusta National"
Similar Articles: None found
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "Major tournament victory, standalone story",
    "category": "Sports",
    "subcategory": "Golf",
    "tags": ["Tiger Woods", "Masters Tournament", "Augusta National", "major championship"]
}

Example 2 - JOIN EXISTING CLUSTER:
Article: "Woods' Masters Victory Breaks 5-Year Major Drought"
Summary: "Tiger Woods' Masters win ends his longest stretch without a major championship since turning pro"
Similar Articles: "Tiger Woods Wins Masters Tournament by 2 Strokes" (similarity: 0.92)
Decision:
{
    "action": "join_existing",
    "cluster_id": "sports-456-def",
    "reason": "Same tournament victory, additional context about drought",
    "category": "Sports",
    "subcategory": "Golf",
    "tags": ["Tiger Woods", "Masters Tournament", "major drought", "comeback"]
}

Example 3 - CREATE NEW (Different event):
Article: "Rory McIlroy Leads PGA Championship After Round 1"
Summary: "Rory McIlroy shot 65 to take early lead at PGA Championship at Baltusrol"
Similar Articles: "Tiger Woods Wins Masters Tournament by 2 Strokes" (similarity: 0.68)
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "Different tournament, different player, different time period",
    "category": "Sports",
    "subcategory": "Golf",
    "tags": ["Rory McIlroy", "PGA Championship", "Baltusrol", "first round lead"]
}""",

            "Business": """
Example 1 - CREATE NEW CLUSTER:
Article: "Tesla Reports Record Q3 Earnings Beat Expectations"
Summary: "Tesla posted quarterly revenue of $25.2B, beating analyst estimates by 8%"
Similar Articles: None found
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "Quarterly earnings report, standalone financial news",
    "category": "Business",
    "subcategory": "Corporate News",
    "tags": ["Tesla", "Q3 earnings", "revenue beat", "financial results"]
}

Example 2 - JOIN EXISTING CLUSTER:
Article: "Tesla Stock Surges 12% After Strong Earnings Report"
Summary: "Tesla shares jumped in after-hours trading following better-than-expected quarterly results"
Similar Articles: "Tesla Reports Record Q3 Earnings Beat Expectations" (similarity: 0.85)
Decision:
{
    "action": "join_existing",
    "cluster_id": "biz-789-ghi",
    "reason": "Market reaction to same earnings report",
    "category": "Business",
    "subcategory": "Markets & Finance",
    "tags": ["Tesla", "stock surge", "earnings reaction", "market response"]
}""",

            "Politics & Government": """
Example 1 - CREATE NEW CLUSTER:
Article: "Senate Passes Bipartisan Infrastructure Bill 69-30"
Summary: "The $1.2 trillion infrastructure package received broad bipartisan support in final Senate vote"
Similar Articles: None found
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "Major legislative passage, new policy story",
    "category": "Politics & Government",
    "subcategory": "Policy & Legislation",
    "tags": ["infrastructure bill", "bipartisan", "Senate vote", "$1.2 trillion"]
}

Example 2 - JOIN EXISTING CLUSTER:
Article: "House Expected to Vote on Infrastructure Bill Next Week"
Summary: "House leadership schedules vote on Senate-passed infrastructure package for Tuesday"
Similar Articles: "Senate Passes Bipartisan Infrastructure Bill 69-30" (similarity: 0.88)
Decision:
{
    "action": "join_existing",
    "cluster_id": "pol-321-jkl",
    "reason": "Same legislation, next step in legislative process",
    "category": "Politics & Government",
    "subcategory": "Policy & Legislation",
    "tags": ["infrastructure bill", "House vote", "legislative process", "scheduling"]
}"""
        }
        
        return examples.get(category, """
Example - CREATE NEW CLUSTER:
Article: "[Title of article about current topic]"
Summary: "[Brief summary of the article content]"
Similar Articles: None found or different topic
Decision:
{
    "action": "create_new",
    "cluster_id": null,
    "reason": "New story or different from existing articles",
    "category": "[Current Category]",
    "subcategory": "[Appropriate subcategory]",
    "tags": ["key-entity", "main-topic", "relevant-theme"]
}

Example - JOIN EXISTING CLUSTER:
Article: "[Related article title]"
Summary: "[Summary of related content]"
Similar Articles: "[Previous article title]" (similarity: 0.85+)
Decision:
{
    "action": "join_existing",
    "cluster_id": "cluster-id-123",
    "reason": "Same story/event, additional details or perspective",
    "category": "[Current Category]",
    "subcategory": "[Appropriate subcategory]",
    "tags": ["shared-entities", "same-topic", "additional-context"]
}""")
    
    def _parse_ai_decision(self, response: str, similar_articles: List[Dict]) -> Dict[str, Any]:
        """Parse AI response into clustering decision"""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            decision = json.loads(response)
            
            # Validate decision
            if decision['action'] not in ['join_existing', 'create_new']:
                raise ValueError("Invalid action")
            
            if decision['action'] == 'join_existing' and not decision.get('cluster_id'):
                # Find the most similar cluster
                if similar_articles:
                    decision['cluster_id'] = similar_articles[0]['cluster_id']
                else:
                    decision['action'] = 'create_new'
            
            return decision
            
        except Exception as e:
            logger.warning(f"Failed to parse AI decision: {str(e)}")
            return {
                'action': 'create_new',
                'reason': 'Failed to parse AI response',
                'category': 'General',
                'subcategory': None,
                'tags': []
            }
    
    def _categorize_article(self, article_data: Dict[str, Any]) -> str:
        """Simple categorization fallback"""
        title_lower = article_data['title'].lower()
        
        if any(word in title_lower for word in ['tech', 'ai', 'apple', 'google', 'microsoft']):
            return 'Technology'
        elif any(word in title_lower for word in ['election', 'president', 'congress', 'politics']):
            return 'Politics'
        elif any(word in title_lower for word in ['stock', 'market', 'economy', 'business']):
            return 'Business'
        elif any(word in title_lower for word in ['health', 'medical', 'covid', 'vaccine']):
            return 'Health'
        else:
            return 'General'
    
    def _create_new_cluster(self, article_data: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Create a new story cluster"""
        cluster_id = str(uuid.uuid4())
        canonical_title = article_data['title']  # Use article title as canonical
        
        try:
            # TODO: Replace with actual model insertion
            # new_cluster = StoryCluster(
            #     cluster_id=cluster_id,
            #     canonical_title=canonical_title,
            #     created_at=datetime.now(timezone.utc)
            # )
            # self.db.add(new_cluster)
            
            # Placeholder implementation
            self.db.execute(
                text("""
                    INSERT INTO story_clusters (cluster_id, canonical_title, created_at)
                    VALUES (:cluster_id, :canonical_title, :created_at)
                """),
                {
                    "cluster_id": cluster_id,
                    "canonical_title": canonical_title,
                    "created_at": datetime.now(timezone.utc)
                }
            )
            
            logger.info(f"Created new story cluster: {cluster_id} - {canonical_title}")
            return cluster_id
            
        except Exception as e:
            logger.error(f"Failed to create new cluster: {str(e)}")
            raise
    
    def _save_article(self, article_data: Dict[str, Any], uniqueness_hash: str, 
                     embedding: np.ndarray, cluster_id: str, decision: Dict[str, Any]) -> str:
        """Save article to database"""
        article_id = str(uuid.uuid4())
        
        try:
            # Convert embedding to list for JSON storage
            embedding_list = embedding.tolist()
            
            # TODO: Replace with actual model insertion
            # new_article = Article(
            #     article_id=article_id,
            #     cluster_id=cluster_id,
            #     url=article_data['url'],
            #     uniqueness_hash=uniqueness_hash,
            #     source_name=article_data['source_name'],
            #     title=article_data['title'],
            #     summary=article_data.get('summary'),
            #     publication_timestamp=article_data.get('published_date'),
            #     category=decision.get('category'),
            #     subcategory=decision.get('subcategory'),
            #     tags=json.dumps(decision.get('tags', [])),
            #     embedding=embedding_list
            # )
            # self.db.add(new_article)
            
            # Placeholder implementation
            self.db.execute(
                text("""
                    INSERT INTO articles (
                        article_id, cluster_id, url, uniqueness_hash, source_name,
                        title, summary, publication_timestamp, category, subcategory,
                        tags, embedding, created_at
                    ) VALUES (
                        :article_id, :cluster_id, :url, :uniqueness_hash, :source_name,
                        :title, :summary, :publication_timestamp, :category, :subcategory,
                        :tags, CAST(:embedding AS vector), :created_at
                    )
                """),
                {
                    "article_id": article_id,
                    "cluster_id": cluster_id,
                    "url": article_data['url'],
                    "uniqueness_hash": uniqueness_hash,
                    "source_name": article_data['source_name'],
                    "title": article_data['title'],
                    "summary": article_data.get('summary'),
                    "publication_timestamp": article_data.get('published_date'),
                    "category": decision.get('category'),
                    "subcategory": decision.get('subcategory'),
                    "tags": json.dumps(decision.get('tags', [])),
                    "embedding": json.dumps(embedding_list),
                    "created_at": datetime.now(timezone.utc)
                }
            )
            
            self.db.commit()
            logger.info(f"Saved article: {article_id}")
            return article_id
            
        except Exception as e:
            logger.error(f"Failed to save article: {str(e)}")
            self.db.rollback()
            raise
