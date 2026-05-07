"""
Knowledge Base Module - Load và search metadata từ main_data.json
Sử dụng semantic similarity để tìm procedures/FAQs liên quan
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import lru_cache
import re


class KnowledgeBase:
    """Knowledge base for HCC Lai Châu procedures and FAQs"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize knowledge base
        
        Args:
            data_path: Path to main_data.json. If None, use default path.
        """
        if data_path is None:
            # Default path: python-server/data/main_data.json
            data_path = Path(__file__).parent.parent / "data" / "main_data.json"
        
        self.data_path = Path(data_path)
        self.data = None
        self.procedures = []
        self.faqs = []
        self.metadata = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.metadata = self.data.get('metadata', {})
            self.procedures = self.data.get('procedures', [])
            self.faqs = self.data.get('citizen_faq', [])
            
            print(f"✅ Knowledge base loaded: {len(self.procedures)} procedures, {len(self.faqs)} FAQs")
            
        except Exception as e:
            print(f"❌ Failed to load knowledge base: {str(e)}")
            self.procedures = []
            self.faqs = []
    
    def search_by_question(self, question: str, top_k: int = 3, min_similarity: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for relevant procedures/FAQs by question
        
        Args:
            question: User question
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of relevant procedures/FAQs with metadata
        """
        # Simple keyword matching (fallback if no semantic search)
        question_lower = question.lower()
        keywords = self._extract_keywords(question_lower)
        
        results = []
        
        # Search in procedures
        for proc in self.procedures:
            score = self._calculate_relevance(proc, keywords, question_lower)
            if score >= min_similarity:
                results.append({
                    'type': 'procedure',
                    'id': proc.get('id'),
                    'name': proc.get('name'),
                    'content': proc.get('content', {}),
                    'score': score,
                    'source': proc.get('source'),
                    'link': proc.get('link')
                })
        
        # Search in FAQs
        for faq in self.faqs:
            score = self._calculate_relevance(faq, keywords, question_lower)
            if score >= min_similarity:
                results.append({
                    'type': 'faq',
                    'id': faq.get('id'),
                    'question': faq.get('question'),
                    'answer': faq.get('answer'),
                    'score': score,
                    'category': faq.get('category')
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Filter out common words (stopwords)
        stopwords = {'là', 'của', 'và', 'có', 'thì', 'được', 'cho', 'với', 'từ', 'trong', 'để', 'như', 'khi', 'nào', 'gì', 'sao', 'thế', 'nào', 'bao', 'nhiêu'}
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        
        return keywords
    
    def _calculate_relevance(self, item: Dict[str, Any], keywords: List[str], question: str) -> float:
        """Calculate relevance score between item and question"""
        score = 0.0
        
        # Get searchable text from item
        if 'name' in item:
            # Procedure
            name = item.get('name', '').lower()
            aliases = ' '.join(item.get('aliases', [])).lower()
            content = item.get('content', {})
            procedure_name = content.get('Tên thủ tục', '').lower()
            requirements = content.get('Yêu cầu điều kiện', '').lower()
            
            searchable = f"{name} {aliases} {procedure_name} {requirements}"
        elif 'question' in item:
            # FAQ
            searchable = f"{item.get('question', '')} {item.get('answer', '')}".lower()
        else:
            return 0.0
        
        # Keyword matching (more strict)
        if keywords:
            keyword_matches = sum(1 for kw in keywords if kw in searchable)
            keyword_score = keyword_matches / len(keywords)
            score += keyword_score * 0.6
        
        # Exact phrase matching
        if question in searchable:
            score += 0.4
        
        # Partial phrase matching (boost for important words)
        important_words = ['đăng ký', 'khai sinh', 'kết hôn', 'hộ chiếu', 'thủ tục', 'giấy tờ']
        for word in important_words:
            if word in question and word in searchable:
                score += 0.1
        
        # Use pre-computed semantic score if available (override if higher)
        if 'semantic_score' in item:
            semantic = item['semantic_score'].get('max_similarity', 0)
            # Only use semantic score if it's significantly higher
            if semantic > score + 0.2:
                score = semantic
        
        return min(score, 1.0)
    
    def get_procedure_by_id(self, proc_id: int) -> Optional[Dict[str, Any]]:
        """Get procedure by ID"""
        for proc in self.procedures:
            if proc.get('id') == proc_id:
                return proc
        return None
    
    def get_faq_by_id(self, faq_id: int) -> Optional[Dict[str, Any]]:
        """Get FAQ by ID"""
        for faq in self.faqs:
            if faq.get('id') == faq_id:
                return faq
        return None
    
    def format_procedure_for_prompt(self, procedure: Dict[str, Any]) -> str:
        """Format procedure for LLM prompt"""
        content = procedure.get('content', {})
        
        formatted = f"""
📋 **Thủ tục: {procedure.get('name')}**

**Yêu cầu điều kiện:**
{content.get('Yêu cầu điều kiện', 'Không có thông tin')}

**Thời hạn giải quyết:**
{content.get('Thời hạn giải quyết', 'Không có thông tin')}

**Phí, lệ phí:**
{content.get('Lệ phí', 'Không có thông tin')}

**Cách thức thực hiện:**
{content.get('Cách thức thực hiện', 'Không có thông tin')[:500]}...

**Kết quả:**
{content.get('Kết quả thực hiện', 'Không có thông tin')}
"""
        return formatted.strip()
    
    def format_faq_for_prompt(self, faq: Dict[str, Any]) -> str:
        """Format FAQ for LLM prompt"""
        formatted = f"""
❓ **Câu hỏi: {faq.get('question')}**

**Trả lời:**
{faq.get('answer', 'Không có thông tin')}
"""
        return formatted.strip()


# Singleton instance
_kb_instance = None

@lru_cache(maxsize=1)
def get_knowledge_base() -> KnowledgeBase:
    """Get singleton knowledge base instance"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance


def search_relevant_knowledge(question: str, top_k: int = 3) -> str:
    """
    Search for relevant knowledge and format for prompt
    
    Args:
        question: User question
        top_k: Number of results
    
    Returns:
        Formatted string with relevant procedures/FAQs
    """
    kb = get_knowledge_base()
    results = kb.search_by_question(question, top_k=top_k)
    
    if not results:
        return "Không tìm thấy thông tin liên quan trong knowledge base."
    
    formatted_parts = ["## 📚 Thông tin tham khảo từ Knowledge Base:\n"]
    
    for i, result in enumerate(results, 1):
        formatted_parts.append(f"\n### {i}. {result.get('name') or result.get('question')} (Score: {result['score']:.2f})")
        
        if result['type'] == 'procedure':
            formatted_parts.append(kb.format_procedure_for_prompt(result))
        else:
            formatted_parts.append(kb.format_faq_for_prompt(result))
    
    return "\n".join(formatted_parts)
