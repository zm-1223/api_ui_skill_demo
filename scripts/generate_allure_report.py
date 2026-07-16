"""手动生成 Allure HTML 报告（根据 reports/allure-results 生成可浏览器打开的 HTML）。"""
import subprocess  # 框架标准库：执行 allure 命令
import sys  # 框架标准库
from pathlib import Path  # 框架标准库

ROOT = Path(__file__).resolve().parent.parent  # 项目根目录
ALLURE_RESULTS = ROOT / "reports" / "allure-results"  # pytest --alluredir 输出
ALLURE_REPORT_DIR = ROOT / "reports" / "allure-report"  # 可浏览器打开的 HTML 目录


def generate_allure_report(combine_single: bool = True) -> int:
    """allure generate 生成 HTML；可选 allure-combine 合并为独立包。"""
    if not ALLURE_RESULTS.exists() or not any(ALLURE_RESULTS.iterdir()):  # 检查结果
        print("错误: reports/allure-results 为空，请先运行: pytest")  # 提示
        return 1  # 失败
    ALLURE_REPORT_DIR.mkdir(parents=True, exist_ok=True)  # 输出目录
    cmd = [
        "allure",
        "generate",
        str(ALLURE_RESULTS),
        "-o",
        str(ALLURE_REPORT_DIR),
        "--clean",
    ]  # Allure CLI
    print("执行:", " ".join(cmd))  # 打印命令
    try:
        result = subprocess.run(cmd, check=False)  # 运行 generate
    except FileNotFoundError:  # 未安装 CLI
        _print_install_help()  # 安装说明
        return 127  # 命令不存在
    if result.returncode != 0:  # generate 失败
        print(f"allure generate 失败，退出码 {result.returncode}")  # 错误
        return result.returncode  # 返回码
    index = ALLURE_REPORT_DIR / "index.html"  # 报告入口
    print(f"\n[OK] Allure HTML 报告:\n  file:///{index.resolve().as_posix()}")  # 双击打开
    if combine_single:  # 可选合并
        _try_combine(ALLURE_REPORT_DIR)  # 合并为更便携的目录内嵌资源
    print(f"\n[提示] pytest-html 报告（无需 Allure CLI）:\n  file:///{(ROOT / 'reports' / 'report.html').resolve().as_posix()}")  # 备用
    return 0  # 成功


def _try_combine(report_dir: Path) -> None:
    """使用 allure-combine 将报告资源内嵌，便于拷贝分享。"""
    try:
        from allure_combine.combine import combine_allure  # 第三方

        combine_allure(
            str(report_dir),
            dest_folder=str(report_dir),
            auto_create_folders=True,
        )  # 原地合并
        print(f"[OK] allure-combine 已内嵌资源，仍从 index.html 打开:\n  file:///{(report_dir / 'index.html').resolve().as_posix()}")  # 提示
    except ImportError:  # 未安装
        print("[跳过] 未安装 allure-combine，目录版报告已可用")  # 说明
    except Exception as exc:  # 合并失败
        print(f"[警告] allure-combine 失败（目录版仍可用）: {exc}")  # 警告


def _print_install_help() -> None:
    """打印 Allure CLI 安装说明。"""
    print(
        "未找到 allure 命令。安装 Allure CLI 后重试:\n"
        "  Windows (scoop): scoop install allure\n"
        "  手动: https://github.com/allure-framework/allure2/releases\n"
        "  解压后将 bin 目录加入 PATH\n\n"
        "无需 Allure 也可查看 pytest-html:\n"
        "  reports/report.html（pytest 运行后自动生成）"
    )  # 帮助文本


if __name__ == "__main__":  # 脚本入口
    sys.exit(generate_allure_report())  # 退出码
