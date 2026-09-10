fetch('/v1/evidence')
  .then((response) => response.ok ? response.json() : Promise.reject(new Error('Evidence unavailable')))
  .then((data) => {
    document.getElementById('raw-tweets').textContent = `${(data.dataset.raw_tweets / 1_000_000).toFixed(2)}M`;
    document.getElementById('spotify-threads').textContent = data.dataset.spotify_threads.toLocaleString();
    document.getElementById('resolved-threads').textContent = data.dataset.resolved_proxy_threads.toLocaleString();
    document.getElementById('retrieval-threads').textContent = data.dataset.retrieval_threads.toLocaleString();
    document.getElementById('safety-score').textContent = `${data.evaluation.safety_gate.passed}/${data.evaluation.safety_gate.total}`;
    document.getElementById('human-labels').textContent = data.evaluation.human_verified_examples;
    document.getElementById('primary-predictions').textContent = data.evaluation.primary_predictions;
    document.getElementById('judge-scores').textContent = data.evaluation.judge_scores;
    document.getElementById('human-ratings').textContent = data.evaluation.paired_human_ratings;
  })
  .catch(() => {});
