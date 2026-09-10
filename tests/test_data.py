from src.data import clean_text, reconstruct


def tweet(id, parent="", inbound=True, author="customer", text="hello", responses=""):
    return dict(
        tweet_id=id,
        in_response_to_tweet_id=parent,
        inbound=inbound,
        author_id=author,
        text=text,
        response_tweet_id=responses,
    )


def test_branching_and_reverse_edges_are_one_component():
    rows = [
        tweet("1", responses="2,3"),
        tweet("2", "1", False, "SpotifyCares"),
        tweet("3", "", False, "SpotifyCares"),
        tweet("4", "2"),
    ]
    threads, stats = reconstruct(rows, "SpotifyCares")
    assert len(threads) == 1
    assert len(threads[0]["tweets"]) == 4
    assert stats["multi_reply_threads"] == 1


def test_missing_parent_and_cycle_are_accounted_for():
    rows = [
        tweet("1", "missing"),
        tweet("2", "1", False, "SpotifyCares"),
        tweet("3", "4"),
        tweet("4", "3", False, "SpotifyCares"),
    ]
    threads, stats = reconstruct(rows, "SpotifyCares")
    assert stats["missing_parent_edges"] == 1
    assert stats["cyclic_components"] == 1
    assert len(threads) == 1


def test_cross_brand_is_excluded():
    rows = [
        tweet("1"),
        tweet("2", "1", False, "SpotifyCares"),
        tweet("3", "1", False, "AmazonHelp"),
    ]
    assert reconstruct(rows, "SpotifyCares")[0] == []


def test_redacts_contact_details_and_routing_handles():
    text = clean_text(
        "@SpotifyCares email me at person@example.com, +1 (212) 555-1234 order AB12345678 https://t.co/test"
    )
    assert "person@" not in text and "555" not in text and "AB12345678" not in text
    assert "@Spotify" not in text and "https://" not in text
