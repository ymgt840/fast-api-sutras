from typing import Any
from starlette import status

class BaseMessage:
    """メッセージの基本クラス"""
    text: str
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, param: Any | None = None) -> None:
        self.param = param

    def __str__(self) -> str:
        return self.__class__.__name__

class ErrorMessage:
    """
    エラーメッセージクラス
    内部クラスでBaseMessageを継承する
    """
    # 共通メッセージ
    class INTERNAL_SERVER_ERROR(BaseMessage):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        text = "システムエラーが発生しました、管理者に問い合わせてください"
    class FAILURE_LOGIN(BaseMessage):
        text = "ログインが失敗しました"
    class NOT_FOUND(BaseMessage):
        test = "{}が見つかりません"
    class ID_NOT_FOUND(BaseMessage):
        status_code = status.HTTP_404_NOT_FOUND
        text = "このidは見つかりません"
    class PARAM_IS_NOT_SET(BaseMessage):
        text = "{}がセットされていません"
    class ALREADY_DELETED(BaseMessage):
        text = "既に削除済です"
    class SOFT_DELETE_NOT_SUPPORTED(BaseMessage):
        text = "論理削除には未対応です"
    class COLUMN_NOT_ALLOWED(BaseMessage):
        text = "このカラムは指定できません"
    # ユーザー系メッセージ
    class ALREADY_REGISTERED_EMAIL(BaseMessage):
        text = "登録済のメールアドレスです"
    class INCORRECT_CURRENT_PASSWORD(BaseMessage):
        text = "現在のパスワードが間違っています"
    class INCORRECT_EMAIL_OR_PASSWORD(BaseMessage):
        status_code = status.HTTP_403_FORBIDDEN
        text = "メールアドレスまたはパスワードが正しくありません"
    class PERMISSION_ERROR(BaseMessage):
        text = "実行権限がありません"
    class CouldNotValidateCredentials(BaseMessage):
        status_code = status.HTTP_403_FORBIDDEN
        text = "認証エラー"