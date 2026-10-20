from evals.run_evals import evaluate_all


def test_golden_dataset_fully_passes():
    report = evaluate_all()
    failures = [r for r in report["results"] if not r["passed"]]
    assert report["total"] >= 10
    assert failures == [], f"Golden eval failures: {failures}"
    assert report["pass_rate"] == 1.0
