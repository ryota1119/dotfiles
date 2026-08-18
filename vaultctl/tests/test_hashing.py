from vaultctl.hashing import canonical_json, canonical_sha256, sha256_bytes, sha256_file

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_bytes_known_value():
    assert sha256_bytes(b"") == EMPTY_SHA256
    assert sha256_bytes(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_sha256_file_matches_bytes_across_chunk_boundary(tmp_path):
    data = b"a" * (1024 * 1024) + b"tail"
    path = tmp_path / "big.bin"
    path.write_bytes(data)
    assert sha256_file(path) == sha256_bytes(data)


def test_canonical_json_is_key_order_stable():
    first = {"b": 1, "a": {"z": True, "y": [3, 2]}}
    second = {"a": {"y": [3, 2], "z": True}, "b": 1}
    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(first) == b'{"a":{"y":[3,2],"z":true},"b":1}'
    assert canonical_sha256(first) == canonical_sha256(second)


def test_canonical_json_keeps_non_ascii_and_has_no_trailing_newline():
    encoded = canonical_json({"title": "第二の脳"})
    assert encoded == '{"title":"第二の脳"}'.encode("utf-8")
    assert not encoded.endswith(b"\n")


def test_canonical_sha256_matches_sha256_of_canonical_json():
    obj = {"schema": "vaultctl.plan.v1", "writes": []}
    assert canonical_sha256(obj) == sha256_bytes(canonical_json(obj))
