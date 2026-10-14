"""Observable retrieval coverage, independent of generated answers and review judgments."""
from collections import Counter

def retrieval_coverage(hits,expected_companies):
    counts=Counter(h['company'] for h in hits)
    expected=list(expected_companies)
    covered=[co for co in expected if counts[co]]
    return dict(expected_companies=expected,retrieved_companies=covered,
                missing_companies=[co for co in expected if not counts[co]],
                unexpected_companies=[co for co in counts if co not in expected],
                company_coverage_count=len(covered),company_coverage_total=len(expected),
                by_company=[dict(company=co,chunk_count=counts[co],chunk_ids=[h['id'] for h in hits if h['company']==co]) for co in expected],
                interpretation='有该公司的块不等于有题目所需指标；证据义务覆盖与答案正确性另行核对。')
