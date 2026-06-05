from fastaction.executor import apply_field_bindings, read_path


def test_read_path_and_apply_field_bindings():
    data = {
        "resource": {"name": "Sample", "status": "active"},
        "metrics": {"progress": 62},
        "items": [{"title": "A"}],
    }

    assert read_path(data, "$.resource.name") == "Sample"
    assert read_path(data, "$.items.0.title") == "A"

    props = apply_field_bindings(
        data,
        {
            "title": "$.resource.name",
            "status": "$.resource.status",
            "metrics.progress": "$.metrics.progress",
            "actions.primary.label": "查看详情",
        },
    )
    assert props == {
        "title": "Sample",
        "status": "active",
        "metrics": {"progress": 62},
        "actions": {"primary": {"label": "查看详情"}},
    }
