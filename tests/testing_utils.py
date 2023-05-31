from typing import Any

def assert_dict_part(
    result_dict: dict[Any, Any],
    expected_dict: dict[Any, Any],
    exclude_fields: list[str] = [],
    is_deleted: bool = False,
) -> None:
    """
    dict のアサーションを実行する
    result_dict と expected_dict の整合性を担保する
    """
    if is_deleted: # 削除済データを取得する場合は、deleted_atにデータが存在することのみをチェックする
        assert result_dict.get("deleted_at") or result_dict.get("deletedAt")
        exclude_fields.extend(["deleted_at", "deletedAt"])

    for key, val in expected_dict.items():
        if key in exclude_fields:
            continue
        # 失敗時に表示されるメッセージを定義する
        msg = f"key={key}, result_value={result_dict.get(key)}, expected_value={val}"
        # assert 実行
        assert result_dict.get(key) == val, msg

def assert_is_deleted(result_dict: dict[Any, Any]) -> None:
    """soft deleted されてる場合 true"""
    assert result_dict.get("deleted_at") is not None

def assert_successful_status_code(status_code: int) -> None:
    """ status_code が成功の場合 true  """
    msg = f"status_code={status_code}. expected: 200 <= status_code < 300"
    assert 200 <= status_code < 300, msg

def assert_failed_status_code(status_code: int) -> None:
    """ status_code が失敗の場合 true """
    msg = f"status_code={status_code}. expected: 200 <= status_code < 300"
    assert not 200 <= status_code < 300, msg

def assert_crud_model(result_obj: Any, expected_obj: Any, exclude_fields: list[str] = []) -> None:
    """ model のassertion を実行する """
    expected_dict = expected_obj.__dict__.copy()
    del expected_dict["_sa_instance_state"] # _sa_instance_state は削除する
    for key, val in expected_dict.items():
        if key in exclude_fields:
            continue
        msg = f"key={key}, result_value={getattr(result_obj, key)}, expected_value={val}"
        assert getattr(result_obj, key) == val, msg