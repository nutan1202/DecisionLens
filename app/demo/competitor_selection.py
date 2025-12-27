"""
Demo competitor selection pipeline that showcases X-Ray capabilities.

This is a mock workflow that simulates:
1. Keyword generation from product description (mock LLM)
2. Candidate search (mock API)
3. Filtering and ranking (business logic)
"""

import random
import re
import time
from app.xray import XRay


# Mock reference product
REFERENCE_PRODUCT = {
    "asin": "B0XYZ123",
    "title": "ProBrand Steel Bottle 32oz Insulated",
    "category": "Sports & Outdoors",
    "price": 29.99,
    "rating": 4.2,
    "reviews": 1247
}

# Mock candidate products (some will pass filters, some won't).
# This is intentionally dummy data for the demo, but we still try to make
# candidate_search correlate with the user's input via simple scoring.
MOCK_CANDIDATES = [
    # Water bottles (Sports & Outdoors)
    {"asin": "B0COMP01", "title": "HydroFlask 32oz Wide Mouth Water Bottle", "category": "Sports & Outdoors", "price": 44.99, "rating": 4.5, "reviews": 8932},
    {"asin": "B0COMP02", "title": "Yeti Rambler 26oz Insulated Bottle", "category": "Sports & Outdoors", "price": 34.99, "rating": 4.4, "reviews": 5621},
    {"asin": "B0COMP03", "title": "Generic Water Bottle 32oz", "category": "Sports & Outdoors", "price": 8.99, "rating": 3.2, "reviews": 45},
    {"asin": "B0COMP07", "title": "Stanley Adventure Quencher Tumbler", "category": "Sports & Outdoors", "price": 35.00, "rating": 4.3, "reviews": 4102},
    {"asin": "B0COMP09", "title": "CamelBak Eddy+ 32oz Water Bottle", "category": "Sports & Outdoors", "price": 24.99, "rating": 4.0, "reviews": 8921},
    {"asin": "B0COMP10", "title": "Nalgene Wide Mouth 32oz Bottle", "category": "Sports & Outdoors", "price": 12.99, "rating": 4.2, "reviews": 15234},

    # Accessories / false positives (still useful for demonstrating filtering)
    {"asin": "B0COMP04", "title": "Bottle Cleaning Brush Set", "category": "Home & Kitchen", "price": 12.99, "rating": 4.6, "reviews": 3421},
    {"asin": "B0COMP05", "title": "Replacement Lid for HydroFlask", "category": "Sports & Outdoors", "price": 9.99, "rating": 4.3, "reviews": 234},
    {"asin": "B0COMP06", "title": "Water Bottle Carrier Bag with Strap", "category": "Sports & Outdoors", "price": 15.99, "rating": 4.1, "reviews": 567},
    {"asin": "B0COMP08", "title": "Premium Titanium Water Bottle", "category": "Sports & Outdoors", "price": 89.00, "rating": 4.8, "reviews": 234},

    # Office chairs (Home & Kitchen / Office)
    {"asin": "B0COMP11", "title": "Ergonomic Office Chair with Lumbar Support", "category": "Home & Kitchen", "price": 159.99, "rating": 4.4, "reviews": 2311},
    {"asin": "B0COMP12", "title": "Mesh Office Chair Adjustable Armrests", "category": "Home & Kitchen", "price": 129.00, "rating": 4.2, "reviews": 5412},
    {"asin": "B0COMP13", "title": "Executive Office Chair High Back Leather", "category": "Home & Kitchen", "price": 199.99, "rating": 4.1, "reviews": 1789},
    {"asin": "B0COMP14", "title": "Seat Cushion for Office Chair Memory Foam", "category": "Home & Kitchen", "price": 39.99, "rating": 4.6, "reviews": 12433},

    # Earbuds (Electronics)
    {"asin": "B0COMP15", "title": "Wireless Bluetooth Earbuds Noise Cancelling", "category": "Electronics", "price": 79.99, "rating": 4.5, "reviews": 5234},
    {"asin": "B0COMP16", "title": "True Wireless Earbuds with Charging Case", "category": "Electronics", "price": 59.99, "rating": 4.2, "reviews": 9321},
    {"asin": "B0COMP17", "title": "Bluetooth Headphones Over Ear Noise Cancelling", "category": "Electronics", "price": 99.99, "rating": 4.4, "reviews": 8112},
    {"asin": "B0COMP18", "title": "Replacement Ear Tips for Earbuds (Pack of 6)", "category": "Electronics", "price": 7.99, "rating": 4.7, "reviews": 21045},

    # Coffee makers (Home & Kitchen)
    {"asin": "B0COMP19", "title": "Stainless Steel Coffee Maker 12 Cup", "category": "Home & Kitchen", "price": 45.00, "rating": 4.3, "reviews": 2891},
    {"asin": "B0COMP20", "title": "Programmable Drip Coffee Maker 12-Cup", "category": "Home & Kitchen", "price": 39.99, "rating": 4.1, "reviews": 17654},
    {"asin": "B0COMP21", "title": "Coffee Filter Paper 100 Pack", "category": "Home & Kitchen", "price": 6.49, "rating": 4.8, "reviews": 50231},
]


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    stop = {"the", "a", "an", "for", "with", "and", "or", "of", "in", "on", "at", "to", "pack", "set"}
    return {t for t in tokens if t not in stop and len(t) > 1}


def _score_candidate(primary_keyword: str, category: str, candidate: dict) -> dict:
    """
    Score a candidate against the search keyword + category.
    This is a demo-friendly, deterministic-ish approximation of what a search API might do.
    """
    kw_tokens = _tokenize(primary_keyword)
    title_tokens = _tokenize(candidate.get("title", ""))
    overlap = sorted(list(kw_tokens & title_tokens))

    # Base relevance = token overlap count
    score = float(len(overlap))

    # Boost if category matches (simple string equality)
    cat_match = bool(category) and (candidate.get("category", "").lower() == (category or "").lower())
    if cat_match:
        score += 1.5

    # Penalize common false-positive accessory terms
    accessory_terms = {"replacement", "lid", "tips", "filter", "paper", "cushion", "brush", "carrier", "bag"}
    accessory_hits = sorted(list(accessory_terms & title_tokens))
    if accessory_hits:
        score -= 1.0

    return {
        "score": round(score, 2),
        "kw_tokens": sorted(list(kw_tokens))[:20],
        "title_tokens_sample": sorted(list(title_tokens))[:20],
        "overlap_tokens": overlap,
        "category_match": cat_match,
        "accessory_hits": accessory_hits,
    }


def run_competitor_selection_demo(
    product_title: str = None,
    category: str = None,
    price: float = None,
    rating: float = None,
    reviews: int = None
) -> str:
    """
    Run the full competitor selection demo pipeline.
    
    Args:
        product_title: Optional custom product title (defaults to REFERENCE_PRODUCT)
        category: Optional custom category (defaults to REFERENCE_PRODUCT)
        price: Optional custom price (defaults to REFERENCE_PRODUCT)
        rating: Optional custom rating (defaults to REFERENCE_PRODUCT)
        reviews: Optional custom review count (defaults to REFERENCE_PRODUCT)
    
    Returns:
        The run_id of the created run
    """
    # Use custom values if provided, otherwise use defaults
    reference_product = {
        "asin": "B0XYZ123",
        "title": product_title or REFERENCE_PRODUCT["title"],
        "category": category or REFERENCE_PRODUCT["category"],
        "price": price if price is not None else REFERENCE_PRODUCT["price"],
        "rating": rating if rating is not None else REFERENCE_PRODUCT["rating"],
        "reviews": reviews if reviews is not None else REFERENCE_PRODUCT["reviews"]
    }
    
    xray = XRay()
    
    with xray.run(
        name="competitor_selection",
        metadata={
            "reference_product": reference_product["asin"],
            "category": reference_product["category"],
            "custom_input": product_title is not None
        }
    ) as run:
        run_id = run.run_id
        
        # Step 1: Keyword Generation
        with run.step(
            name="keyword_generation",
            input_data={
                "product_title": reference_product["title"],
                "category": reference_product["category"]
            },
            reasoning=f"Extracting key product attributes from '{reference_product['title']}' in category '{reference_product['category']}'"
        ) as step:
            # Simulate LLM call delay
            time.sleep(0.1)
            
            # Generate keywords from the product title (mock LLM - simple keyword extraction)
            title_lower = reference_product["title"].lower()
            words = title_lower.split()
            
            # Remove common words to get important keywords
            common_words = {"the", "a", "an", "for", "with", "and", "or", "of", "in", "on", "at", "to"}
            important_words = [w for w in words if w not in common_words]
            
            # Create variations of the product title
            keywords = [
                reference_product["title"].lower(),  # Full title lowercase
            ]
            
            # Add variations based on important words
            if len(important_words) >= 1:
                keywords.append(" ".join(important_words))  # All important words
            if len(important_words) >= 2:
                keywords.append(" ".join(important_words[:3]))  # Top 3 important words
                keywords.append(" ".join(important_words[:2]))  # Top 2 important words
            if len(important_words) >= 1:
                keywords.append(important_words[0])  # Single most important word
            
            # Add category-based keyword
            if reference_product["category"] and len(important_words) >= 1:
                keywords.append(f"{' '.join(important_words[:2])} {reference_product['category'].lower()}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for kw in keywords:
                if kw and kw not in seen:
                    seen.add(kw)
                    unique_keywords.append(kw)
            
            keywords = unique_keywords[:5]  # Limit to 5 keywords
            
            step.set_output({
                "keywords": keywords,
                "model": "gpt-4"
            })
        
        # Step 2: Candidate Search
        with run.step(
            name="candidate_search",
            input_data={
                "keywords": keywords,
                "primary_keyword": keywords[0],
                "limit": 50
            },
            reasoning=f"Searched for '{keywords[0]}' and ranked candidates by keyword overlap + category match"
        ) as step:
            # Simulate API call delay
            time.sleep(0.15)

            primary_keyword = keywords[0]
            reference_category = reference_product.get("category", "")

            # Score every candidate (mock search ranking)
            scored = []
            for c in MOCK_CANDIDATES:
                score_detail = _score_candidate(primary_keyword, reference_category, c)
                scored.append((score_detail["score"], score_detail, c))

            # Sort: higher score first; deterministic tie-breaker by reviews
            scored.sort(key=lambda t: (t[0], t[2].get("reviews", 0)), reverse=True)

            # Pick top-N candidates (simulate search limit)
            top_n = 8
            candidates = [t[2] for t in scored[:top_n]]

            # Record scoring details as evaluations so dashboard shows "why" these candidates surfaced
            evaluations = []
            for rank, (score, score_detail, c) in enumerate(scored[:min(len(scored), 20)], start=1):
                evaluations.append({
                    "asin": c.get("asin"),
                    "title": c.get("title"),
                    "metrics": {
                        "price": c.get("price"),
                        "rating": c.get("rating"),
                        "reviews": c.get("reviews"),
                    },
                    "filter_results": {
                        "keyword_overlap": {
                            "passed": len(score_detail["overlap_tokens"]) > 0,
                            "detail": f"overlap={len(score_detail['overlap_tokens'])} tokens={score_detail['overlap_tokens']}"
                        },
                        "category_match": {
                            "passed": bool(score_detail["category_match"]),
                            "detail": f"candidate_category='{c.get('category', '')}' vs reference_category='{reference_category}'"
                        },
                        "accessory_penalty": {
                            "passed": len(score_detail["accessory_hits"]) == 0,
                            "detail": f"accessory_hits={score_detail['accessory_hits']}"
                        },
                        "total_score": {
                            "passed": True,
                            "detail": f"rank={rank} score={score_detail['score']}"
                        }
                    },
                    "qualified": rank <= top_n  # "qualified" means returned in top-N
                })

            step.add_evaluations(evaluations)

            # Mock total results (stable-ish, but still variable)
            mock_total = max(50, min(5000, int(250 + len(_tokenize(primary_keyword)) * 400)))

            step.set_output({
                "total_results": mock_total,
                "candidates_fetched": len(candidates),
                "search_keywords_used": keywords,
                "ranking_method": "token_overlap + category_boost - accessory_penalty",
                "candidates": candidates
            })
        
        # Step 3: Apply Filters and Select
        with run.step(
            name="apply_filters_and_select",
            input_data={
                "candidates_count": len(candidates),
                "reference_product": reference_product
            },
            reasoning="Applying price, rating, and review count filters to narrow candidates"
        ) as step:
            # Define filters
            price_min = reference_product["price"] * 0.5
            price_max = reference_product["price"] * 2.0
            min_rating = 3.8
            min_reviews = 100
            
            filters_applied = {
                "price_range": {
                    "min": price_min,
                    "max": price_max,
                    "rule": "0.5x - 2x of reference price"
                },
                "min_rating": {
                    "value": min_rating,
                    "rule": "Must be at least 3.8 stars"
                },
                "min_reviews": {
                    "value": min_reviews,
                    "rule": "Must have at least 100 reviews"
                }
            }
            
            step.set_filters(filters_applied)
            
            # Evaluate each candidate
            evaluations = []
            qualified_candidates = []
            
            for candidate in candidates:
                # Check each filter
                price_passed = price_min <= candidate["price"] <= price_max
                rating_passed = candidate["rating"] >= min_rating
                reviews_passed = candidate["reviews"] >= min_reviews
                
                filter_results = {
                    "price_range": {
                        "passed": price_passed,
                        "detail": f"${candidate['price']:.2f} is {'within' if price_passed else 'outside'} ${price_min:.2f}-${price_max:.2f}"
                    },
                    "min_rating": {
                        "passed": rating_passed,
                        "detail": f"{candidate['rating']} {'>=' if rating_passed else '<'} {min_rating}"
                    },
                    "min_reviews": {
                        "passed": reviews_passed,
                        "detail": f"{candidate['reviews']} {'>=' if reviews_passed else '<'} {min_reviews} minimum"
                    }
                }
                
                qualified = price_passed and rating_passed and reviews_passed
                
                evaluation = {
                    "asin": candidate["asin"],
                    "title": candidate["title"],
                    "metrics": {
                        "price": candidate["price"],
                        "rating": candidate["rating"],
                        "reviews": candidate["reviews"]
                    },
                    "filter_results": filter_results,
                    "qualified": qualified
                }
                
                evaluations.append(evaluation)
                
                if qualified:
                    qualified_candidates.append(candidate)
            
            step.add_evaluations(evaluations)
            
            # Select best candidate (highest review count among qualified)
            if qualified_candidates:
                selected = max(qualified_candidates, key=lambda c: c["reviews"])
                
                step.set_output({
                    "total_evaluated": len(candidates),
                    "passed": len(qualified_candidates),
                    "failed": len(candidates) - len(qualified_candidates),
                    "selected_competitor": selected,
                    "selection_reason": f"Highest review count ({selected['reviews']}) among qualified candidates"
                })
            else:
                step.set_output({
                    "total_evaluated": len(candidates),
                    "passed": 0,
                    "failed": len(candidates),
                    "selected_competitor": None,
                    "selection_reason": "No candidates passed all filters"
                })
            
            # Simulate processing delay
            time.sleep(0.1)
        
        return run_id

