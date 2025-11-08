from ob1.path_filters import matches_any, parse_scope


def test_parse_scope_defaults():
    assert parse_scope(None) == ["**"]
    assert parse_scope("") == ["**"]


def test_parse_scope_splitters():
    assert parse_scope("frontend/**, web/**/*") == ["frontend/**", "web/**/*"]
    assert parse_scope("frontend/**;server/**") == ["frontend/**", "server/**"]


def test_matches_any():
    patterns = ["frontend/**", "web/*.js"]
    assert matches_any("frontend/src/App.jsx", patterns)
    assert not matches_any("api/server.ts", patterns)
