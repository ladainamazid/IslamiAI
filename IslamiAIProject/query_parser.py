# File: query_parser.py (UPDATED)
# Parse user query dan match ke topic menggunakan keyword matching

from islamic_data import shafii_rules

def parse_user_query(question):
    """
    Parse user question dan return topic yang paling match
    Menggunakan keyword matching dari shafii_rules entries
    
    Args:
        question (str): Pertanyaan user
    
    Returns:
        str: topic key yang match, atau None jika tidak ada match
    """
    
    # Normalize question: lowercase dan split
    question_lower = question.lower()
    question_words = set(question_lower.split())
    
    best_match = None
    best_score = 0
    
    # Iterate semua entries di shafii_rules
    for topic_key, rule in shafii_rules.items():
        keywords = rule.get("keywords", [])
        
        if not keywords:
            continue
        
        # Hitung matching score
        match_score = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            keyword_words = set(keyword_lower.split())
            
            # Check if keyword or any word in keyword matches
            if keyword_lower in question_lower:
                match_score += 2  # Exact match dalam question
            
            # Check word overlap
            overlap = question_words.intersection(keyword_words)
            if overlap:
                match_score += len(overlap)  # Count overlapping words
        
        # Update best match
        if match_score > best_score:
            best_score = match_score
            best_match = topic_key
    
    return best_match

def parse_user_query_debug(question):
    """
    Debug version: return semua matches dengan score
    """
    question_lower = question.lower()
    question_words = set(question_lower.split())
    
    matches = {}
    
    for topic_key, rule in shafii_rules.items():
        keywords = rule.get("keywords", [])
        
        if not keywords:
            continue
        
        match_score = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            keyword_words = set(keyword_lower.split())
            
            if keyword_lower in question_lower:
                match_score += 2
            
            overlap = question_words.intersection(keyword_words)
            if overlap:
                match_score += len(overlap)
        
        if match_score > 0:
            matches[topic_key] = {
                "score": match_score,
                "keywords": keywords
            }
    
    # Sort by score
    sorted_matches = sorted(matches.items(), key=lambda x: x[1]["score"], reverse=True)
    return sorted_matches

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "syahadat",
        "apa itu tauhid",
        "boleh wudhu sebelum shalat",
        "hukum daging halal",
        "apakah boleh berdagang online",
        "hukum pernikahan dengan kafir"
    ]
    
    print("=== Query Parser Test ===\n")
    
    for query in test_queries:
        result = parse_user_query(query)
        print(f"Query: '{query}'")
        print(f"Match: {result}")
        
        # Debug
        debug = parse_user_query_debug(query)
        if debug:
            print(f"Top 3 matches:")
            for topic, data in debug[:3]:
                print(f"  - {topic} (score: {data['score']})")
        print()
