import logging
import psycopg2
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from agent.config import settings

logger = logging.getLogger(__name__)

class SmartArticleService:
    def __init__(self):
        """Initialize smart article service with database connection"""
        self.db_config = self._parse_database_url(settings.database_url)
    
    def _parse_database_url(self, database_url: str) -> dict:
        """Parse PostgreSQL database URL into connection components"""
        # Format: postgresql://user:password@host:port/database
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path[1:]  # Remove leading /
        }
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_articles_for_podcast(
        self,
        selected_categories: List[str],
        selected_subcategories: Optional[List[str]] = None,
        total_articles: int = 15,
        min_importance_score: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Smart article selection for podcast generation based on user preferences
        
        Args:
            selected_categories: List of category names user selected
            selected_subcategories: Optional list of subcategory names to include
            total_articles: Total number of articles to return
            min_importance_score: Minimum importance score to include (1-10)
        
        Returns:
            List of article dictionaries optimally distributed across categories
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Calculate articles per category
            num_categories = len(selected_categories)
            if num_categories == 0:
                logger.warning("No categories selected")
                return []
            
            articles_per_category = max(1, total_articles // num_categories)
            remainder = total_articles % num_categories
            
            logger.info(f"Distributing {total_articles} articles across {num_categories} categories:")
            logger.info(f"Base: {articles_per_category} per category, +{remainder} extra")
            
            all_articles = []
            
            for i, category in enumerate(selected_categories):
                # Calculate how many articles for this category
                category_limit = articles_per_category
                if i < remainder:  # Distribute remainder to first categories
                    category_limit += 1
                
                logger.info(f"Getting {category_limit} articles for {category}")
                
                # Build category-specific query
                query_conditions = [
                    "a.category = %s", 
                    "sc.importance_score >= %s"
                ]
                query_params = [category, min_importance_score]
                
                # Add subcategory filter if specified
                if selected_subcategories:
                    query_conditions.append("a.subcategory = ANY(%s)")
                    query_params.append(selected_subcategories)
                
                # Query for highest importance stories in this category
                query = f"""
                SELECT DISTINCT ON (a.cluster_id)
                    a.article_id,
                    a.cluster_id,
                    a.url,
                    a.source_name,
                    a.title,
                    a.summary,
                    a.publication_timestamp,
                    a.category,
                    a.subcategory,
                    a.tags,
                    a.created_at,
                    sc.canonical_title as story_title,
                    sc.importance_score
                FROM articles a
                INNER JOIN story_clusters sc ON a.cluster_id = sc.cluster_id
                WHERE {' AND '.join(query_conditions)}
                ORDER BY a.cluster_id, sc.importance_score DESC
                LIMIT %s
                """
                
                query_params.append(category_limit * 2)  # Get extra to ensure diversity
                
                cur.execute(query, query_params)
                category_results = cur.fetchall()
                
                # Sort by importance score and take the best ones
                sorted_results = sorted(category_results, key=lambda x: x[12], reverse=True)  # importance_score is index 12
                top_results = sorted_results[:category_limit]
                
                logger.info(f"Found {len(top_results)} articles for {category}")
                
                for row in top_results:
                    article = {
                        'article_id': row[0],
                        'cluster_id': row[1],
                        'url': row[2],
                        'source_name': row[3],
                        'title': row[4],
                        'summary': row[5],
                        'publication_timestamp': row[6].isoformat() if row[6] else None,
                        'category': row[7],
                        'subcategory': row[8],
                        'tags': row[9] or [],
                        'created_at': row[10].isoformat() if row[10] else None,
                        'story_title': row[11],
                        'importance_score': row[12]
                    }
                    all_articles.append(article)
            
            cur.close()
            conn.close()
            
            # Final sort by importance score across all categories
            final_articles = sorted(all_articles, key=lambda x: x['importance_score'], reverse=True)
            
            logger.info(f"Selected {len(final_articles)} total articles for podcast")
            if final_articles:
                score_range = f"{min(a['importance_score'] for a in final_articles)}-{max(a['importance_score'] for a in final_articles)}"
                logger.info(f"Importance score range: {score_range}")
            
            return final_articles[:total_articles]  # Ensure we don't exceed the limit
            
        except Exception as e:
            logger.error(f"Error getting articles for podcast: {str(e)}")
            return []
    
    def get_articles_by_subcategories(
        self,
        selected_subcategories: List[str],
        total_articles: int = 8,
        min_importance_score: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get articles filtered purely by subcategories (regardless of parent category)
        
        Args:
            selected_subcategories: List of subcategory names to include
            total_articles: Total number of articles to return
            min_importance_score: Minimum importance score to include (1-10)
        
        Returns:
            List of article dictionaries from the specified subcategories
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            if not selected_subcategories:
                logger.warning("No subcategories selected")
                return []
            
            # Query for highest importance articles in the selected subcategories
            query = """
            SELECT DISTINCT ON (a.cluster_id)
                a.article_id,
                a.cluster_id,
                a.url,
                a.source_name,
                a.title,
                a.summary,
                a.publication_timestamp,
                a.category,
                a.subcategory,
                a.tags,
                a.created_at,
                sc.canonical_title as story_title,
                sc.importance_score
            FROM articles a
            INNER JOIN story_clusters sc ON a.cluster_id = sc.cluster_id
            WHERE a.subcategory = ANY(%s) 
            AND sc.importance_score >= %s
            ORDER BY a.cluster_id, sc.importance_score DESC
            LIMIT %s
            """
            
            cur.execute(query, (selected_subcategories, min_importance_score, total_articles * 2))
            results = cur.fetchall()
            
            # Sort by importance score and take the best ones
            sorted_results = sorted(results, key=lambda x: x[12], reverse=True)  # importance_score is index 12
            top_results = sorted_results[:total_articles]
            
            articles = []
            for row in top_results:
                article = {
                    'article_id': row[0],
                    'cluster_id': row[1],
                    'url': row[2],
                    'source_name': row[3],
                    'title': row[4],
                    'summary': row[5],
                    'publication_timestamp': row[6].isoformat() if row[6] else None,
                    'category': row[7],
                    'subcategory': row[8],
                    'tags': row[9] or [],
                    'created_at': row[10].isoformat() if row[10] else None,
                    'story_title': row[11],
                    'importance_score': row[12]
                }
                articles.append(article)
            
            cur.close()
            conn.close()
            
            logger.info(f"Selected {len(articles)} articles from subcategories: {selected_subcategories}")
            if articles:
                score_range = f"{min(a['importance_score'] for a in articles)}-{max(a['importance_score'] for a in articles)}"
                logger.info(f"Importance score range: {score_range}")
                
                # Log subcategory distribution
                subcat_counts = {}
                for article in articles:
                    subcat = article['subcategory']
                    subcat_counts[subcat] = subcat_counts.get(subcat, 0) + 1
                logger.info(f"Distribution: {dict(subcat_counts)}")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles by subcategories: {str(e)}")
            return []
    
    def get_available_categories(self) -> List[Dict[str, Any]]:
        """Get all available categories and their subcategories with article counts and importance stats"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Get categories with article counts, importance stats, and recent subcategories
            query = """
            SELECT 
                a.category,
                a.subcategory,
                COUNT(*) as article_count,
                AVG(sc.importance_score) as avg_importance,
                MAX(sc.importance_score) as max_importance,
                MAX(a.publication_timestamp) as latest_article
            FROM articles a
            INNER JOIN story_clusters sc ON a.cluster_id = sc.cluster_id
            WHERE a.publication_timestamp >= %s
            GROUP BY a.category, a.subcategory
            ORDER BY a.category, avg_importance DESC, article_count DESC
            """
            
            # Look back 7 days for available categories
            cutoff_time = datetime.now() - timedelta(days=7)
            cur.execute(query, (cutoff_time,))
            
            # Organize results by category
            categories = {}
            for row in cur.fetchall():
                category, subcategory, count, avg_importance, max_importance, latest = row
                
                if category not in categories:
                    categories[category] = {
                        'category': category,
                        'subcategories': [],
                        'total_articles': 0,
                        'avg_importance': 0,
                        'max_importance': 0
                    }
                
                categories[category]['subcategories'].append({
                    'subcategory': subcategory,
                    'article_count': count,
                    'avg_importance': round(avg_importance, 1) if avg_importance else 5.0,
                    'max_importance': max_importance or 5,
                    'latest_article': latest.isoformat() if latest else None
                })
                categories[category]['total_articles'] += count
                
            # Calculate category-level importance scores
            for cat_data in categories.values():
                if cat_data['subcategories']:
                    cat_data['avg_importance'] = round(
                        sum(sub['avg_importance'] * sub['article_count'] 
                            for sub in cat_data['subcategories']) / cat_data['total_articles'], 1
                    )
                    cat_data['max_importance'] = max(sub['max_importance'] 
                                                   for sub in cat_data['subcategories'])
            
            cur.close()
            conn.close()
            
            result = list(categories.values())
            # Sort by average importance score
            result.sort(key=lambda x: x['avg_importance'], reverse=True)
            
            logger.info(f"Found {len(result)} categories with recent articles")
            return result
            
        except Exception as e:
            logger.error(f"Error getting available categories: {str(e)}")
            return []
    
    def get_top_stories_by_importance(
        self, 
        limit: int = 10, 
        min_importance: int = 7,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Get top stories by importance score for breaking news or highlights"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            query = """
            SELECT DISTINCT ON (a.cluster_id)
                a.article_id,
                a.cluster_id,
                a.url,
                a.source_name,
                a.title,
                a.summary,
                a.publication_timestamp,
                a.category,
                a.subcategory,
                a.tags,
                sc.canonical_title as story_title,
                sc.importance_score
            FROM articles a
            INNER JOIN story_clusters sc ON a.cluster_id = sc.cluster_id
            WHERE a.publication_timestamp >= %s 
            AND sc.importance_score >= %s
            ORDER BY a.cluster_id, sc.importance_score DESC, a.publication_timestamp DESC
            """
            
            cur.execute(query, (cutoff_time, min_importance))
            results = cur.fetchall()
            
            # Sort by importance score and take top stories
            sorted_results = sorted(results, key=lambda x: x[11], reverse=True)  # importance_score is index 11
            top_stories = sorted_results[:limit]
            
            articles = []
            for row in top_stories:
                article = {
                    'article_id': row[0],
                    'cluster_id': row[1],
                    'url': row[2],
                    'source_name': row[3],
                    'title': row[4],
                    'summary': row[5],
                    'publication_timestamp': row[6].isoformat() if row[6] else None,
                    'category': row[7],
                    'subcategory': row[8],
                    'tags': row[9] or [],
                    'story_title': row[10],
                    'importance_score': row[11]
                }
                articles.append(article)
            
            cur.close()
            conn.close()
            
            logger.info(f"Found {len(articles)} top stories with importance >= {min_importance}")
            return articles
            
        except Exception as e:
            logger.error(f"Error getting top stories: {str(e)}")
            return []
    
    def get_article_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about articles in the database"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Get overall stats
            stats_query = """
            SELECT 
                COUNT(*) as total_articles,
                COUNT(DISTINCT a.cluster_id) as unique_stories,
                COUNT(DISTINCT a.category) as categories,
                AVG(sc.importance_score) as avg_importance,
                MIN(a.publication_timestamp) as oldest_article,
                MAX(a.publication_timestamp) as newest_article
            FROM articles a
            INNER JOIN story_clusters sc ON a.cluster_id = sc.cluster_id
            """
            
            cur.execute(stats_query)
            row = cur.fetchone()
            
            stats = {
                'total_articles': row[0],
                'unique_stories': row[1], 
                'categories_count': row[2],
                'avg_importance_score': round(row[3], 2) if row[3] else 5.0,
                'oldest_article': row[4].isoformat() if row[4] else None,
                'newest_article': row[5].isoformat() if row[5] else None
            }
            
            # Get importance score distribution
            importance_query = """
            SELECT 
                sc.importance_score,
                COUNT(*) as story_count
            FROM story_clusters sc
            GROUP BY sc.importance_score
            ORDER BY sc.importance_score
            """
            
            cur.execute(importance_query)
            importance_distribution = {}
            for row in cur.fetchall():
                importance_distribution[row[0]] = row[1]
            
            stats['importance_distribution'] = importance_distribution
            
            # Get recent articles count (last 24 hours)
            recent_query = """
            SELECT COUNT(*) FROM articles 
            WHERE publication_timestamp >= %s
            """
            
            cutoff_time = datetime.now() - timedelta(hours=24)
            cur.execute(recent_query, (cutoff_time,))
            stats['recent_articles_24h'] = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting article stats: {str(e)}")
            return {}
