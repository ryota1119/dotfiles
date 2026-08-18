from vaultctl.findings import Finding, sort_findings


def test_sort_findings_orders_by_rule_then_path_then_message():
    a = Finding("2", "violation", "wiki/concepts/b.md", "updated が created より前です")
    b = Finding("1", "violation", "wiki/concepts/b.md", "必須キーがありません: tags")
    c = Finding("1", "violation", "wiki/concepts/a.md", "未定義のキーです: address")
    d = Finding("1", "violation", "wiki/concepts/a.md", "必須キーがありません: title")

    # 「必」(U+5FC5) < 「未」(U+672A) なので同一パス内では d が c より先に来る
    assert sort_findings([a, b, c, d]) == [d, c, b, a]


def test_sort_findings_returns_new_list_and_keeps_input_intact():
    src = [
        Finding("3", "violation", "wiki/sources/x.md", "type=concept は wiki/concepts/ に置く必要があります"),
        Finding("1", "violation", "wiki/sources/x.md", "必須キーがありません: tags"),
    ]
    original = list(src)
    result = sort_findings(src)

    assert src == original
    assert result[0].rule == "1"
    assert isinstance(result, list)


def test_finding_is_frozen_and_hashable():
    f = Finding("5", "violation", "wiki/concepts/a.md", "どこからもリンクされていません")
    assert {f, Finding("5", "violation", "wiki/concepts/a.md", "どこからもリンクされていません")} == {f}
