"""命令行界面工具"""

import json
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.json import JSON

from .client import StandardLLMClient, LLMClientPool
from .config import StandardConfig, ModelConfig
from .exceptions import LLMStandardError

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def main():
    """LLM指令遵循與結構化輸出標準庫命令行工具"""
    pass


@main.command()
@click.option('--provider', '-p', required=True, 
              type=click.Choice(['openai', 'anthropic', 'google', 'deepseek']),
              help='LLM提供商')
@click.option('--model', '-m', help='模型名稱')
@click.option('--api-key', '-k', help='API密鑰')
@click.option('--base-url', help='API基礎URL')
@click.option('--timeout', default=30, help='請求超時時間（秒）')
def test_connection(provider: str, model: Optional[str], api_key: Optional[str], 
                   base_url: Optional[str], timeout: int):
    """測試LLM提供商連接"""
    try:
        # 創建客戶端
        client = StandardLLMClient(
            provider=provider,
            api_key=api_key or click.prompt(f'請輸入{provider}的API密鑰', hide_input=True),
            model=model or _get_default_model(provider),
            base_url=base_url,
            timeout=timeout
        )
        
        console.print(f"[yellow]正在測試{provider}連接...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("連接測試中...", total=None)
            
            # 執行健康檢查
            start_time = time.time()
            health_result = client.health_check()
            response_time = time.time() - start_time
            
            progress.update(task, completed=True)
        
        if health_result['status'] == 'healthy':
            console.print("[green]✅ 連接成功！[/green]")
            
            # 顯示詳細信息
            table = Table(title=f"{provider.title()} 連接信息")
            table.add_column("項目", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("提供商", provider)
            table.add_row("模型", client.model)
            table.add_row("響應時間", f"{response_time:.2f}秒")
            table.add_row("狀態", "健康")
            
            if 'model_info' in health_result:
                model_info = health_result['model_info']
                table.add_row("模型版本", model_info.get('version', 'N/A'))
                table.add_row("最大Token", str(model_info.get('max_tokens', 'N/A')))
            
            console.print(table)
        else:
            console.print("[red]❌ 連接失敗！[/red]")
            console.print(f"錯誤: {health_result.get('error', '未知錯誤')}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ 連接測試失敗: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('--input-file', '-i', type=click.Path(exists=True), help='輸入文件路徑')
@click.option('--output-file', '-o', type=click.Path(), help='輸出文件路徑')
@click.option('--provider', '-p', required=True,
              type=click.Choice(['openai', 'anthropic', 'google', 'deepseek']),
              help='LLM提供商')
@click.option('--model', '-m', help='模型名稱')
@click.option('--api-key', '-k', help='API密鑰')
@click.option('--instruction-type', '-t', default='structured_output',
              type=click.Choice(['structured_output', 'text_analysis', 'extraction', 'generation']),
              help='指令類型')
@click.option('--schema-file', '-s', type=click.Path(exists=True), help='JSON Schema文件路徑')
@click.option('--description', '-d', help='任務描述')
@click.option('--constraints', '-c', multiple=True, help='約束條件')
@click.option('--validate/--no-validate', default=True, help='是否驗證輸出')
@click.argument('text', required=False)
def execute(input_file: Optional[str], output_file: Optional[str], provider: str,
           model: Optional[str], api_key: Optional[str], instruction_type: str,
           schema_file: Optional[str], description: Optional[str],
           constraints: List[str], validate: bool, text: Optional[str]):
    """執行LLM指令"""
    try:
        # 獲取輸入文本
        if input_file:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_text = f.read().strip()
        elif text:
            input_text = text
        else:
            input_text = click.prompt('請輸入文本')
        
        # 加載Schema
        if schema_file:
            with open(schema_file, 'r', encoding='utf-8') as f:
                output_schema = json.load(f)
        else:
            output_schema = _get_default_schema(instruction_type)
        
        # 創建客戶端
        client = StandardLLMClient(
            provider=provider,
            api_key=api_key or click.prompt(f'請輸入{provider}的API密鑰', hide_input=True),
            model=model or _get_default_model(provider),
            validate_responses=validate
        )
        
        # 創建指令
        instruction = client.create_instruction(
            instruction_type=instruction_type,
            description=description or f"執行{instruction_type}任務",
            output_schema=output_schema,
            constraints=list(constraints) if constraints else None
        )
        
        console.print(f"[yellow]正在執行{instruction_type}任務...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("處理中...", total=None)
            
            # 執行指令
            start_time = time.time()
            response = client.execute(instruction, input_text)
            processing_time = time.time() - start_time
            
            progress.update(task, completed=True)
        
        if response['status'] == 'success':
            console.print("[green]✅ 執行成功！[/green]")
            
            # 顯示結果
            result_panel = Panel(
                JSON.from_data(response['data']),
                title="執行結果",
                border_style="green"
            )
            console.print(result_panel)
            
            # 顯示元數據
            metadata = response['metadata']
            meta_table = Table(title="執行信息")
            meta_table.add_column("項目", style="cyan")
            meta_table.add_column("值", style="yellow")
            
            meta_table.add_row("處理時間", f"{processing_time:.2f}秒")
            meta_table.add_row("Token使用", str(metadata['token_usage']['total_tokens']))
            meta_table.add_row("模型", f"{metadata['model_info']['provider']}/{metadata['model_info']['model']}")
            
            if 'confidence_score' in metadata:
                meta_table.add_row("置信度", f"{metadata['confidence_score']:.2f}")
            
            console.print(meta_table)
            
            # 保存結果
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(response, f, indent=2, ensure_ascii=False)
                console.print(f"[green]結果已保存到: {output_file}[/green]")
        
        else:
            console.print("[red]❌ 執行失敗！[/red]")
            for error in response['errors']:
                console.print(f"錯誤: {error['message']}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ 執行失敗: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('--config-file', '-c', type=click.Path(), help='配置文件路徑')
@click.option('--providers', '-p', multiple=True,
              type=click.Choice(['openai', 'anthropic', 'google', 'deepseek']),
              help='要測試的提供商')
@click.option('--iterations', '-n', default=5, help='測試迭代次數')
@click.option('--concurrent', default=1, help='並發數')
def benchmark(config_file: Optional[str], providers: List[str], 
             iterations: int, concurrent: int):
    """性能基準測試"""
    try:
        # 加載配置
        if config_file:
            config = StandardConfig.from_file(config_file)
        else:
            config = StandardConfig.from_env()
        
        # 確定要測試的提供商
        test_providers = list(providers) if providers else list(config.models.keys())
        
        if not test_providers:
            console.print("[red]❌ 沒有可用的提供商配置[/red]")
            sys.exit(1)
        
        console.print(f"[yellow]開始性能基準測試...[/yellow]")
        console.print(f"提供商: {', '.join(test_providers)}")
        console.print(f"迭代次數: {iterations}")
        console.print(f"並發數: {concurrent}")
        
        # 測試指令
        instruction = {
            "instruction_type": "structured_output",
            "version": "1.0",
            "task": {
                "description": "生成產品信息"
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "category": {"type": "string"}
                },
                "required": ["name", "price", "category"]
            }
        }
        
        test_input = "生成一個智能手機產品信息"
        
        results = {}
        
        for provider in test_providers:
            console.print(f"\n[cyan]測試 {provider}...[/cyan]")
            
            model_config = config.get_model_config(provider)
            if not model_config:
                console.print(f"[red]跳過 {provider}: 沒有配置[/red]")
                continue
            
            client = StandardLLMClient(
                provider=provider,
                api_key=model_config.api_key,
                model=model_config.model
            )
            
            times = []
            tokens = []
            success_count = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"測試 {provider}", total=iterations)
                
                for i in range(iterations):
                    try:
                        start_time = time.time()
                        response = client.execute(instruction, test_input)
                        end_time = time.time()
                        
                        if response['status'] == 'success':
                            success_count += 1
                            times.append(end_time - start_time)
                            tokens.append(response['metadata']['token_usage']['total_tokens'])
                        
                        progress.update(task, advance=1)
                        
                    except Exception as e:
                        console.print(f"[red]迭代 {i+1} 失敗: {e}[/red]")
                        progress.update(task, advance=1)
            
            if times:
                results[provider] = {
                    'success_rate': success_count / iterations,
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'avg_tokens': sum(tokens) / len(tokens) if tokens else 0,
                    'total_requests': iterations,
                    'successful_requests': success_count
                }
        
        # 顯示結果
        if results:
            console.print("\n[green]基準測試結果:[/green]")
            
            table = Table(title="性能基準測試結果")
            table.add_column("提供商", style="cyan")
            table.add_column("成功率", style="green")
            table.add_column("平均時間", style="yellow")
            table.add_column("最快時間", style="blue")
            table.add_column("最慢時間", style="red")
            table.add_column("平均Token", style="magenta")
            
            for provider, result in results.items():
                table.add_row(
                    provider,
                    f"{result['success_rate']:.1%}",
                    f"{result['avg_time']:.2f}s",
                    f"{result['min_time']:.2f}s",
                    f"{result['max_time']:.2f}s",
                    f"{result['avg_tokens']:.0f}"
                )
            
            console.print(table)
        else:
            console.print("[red]❌ 沒有成功的測試結果[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ 基準測試失敗: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('--output', '-o', default='config.json', help='輸出配置文件路徑')
def init_config(output: str):
    """初始化配置文件"""
    try:
        config = StandardConfig()
        
        console.print("[yellow]初始化配置文件...[/yellow]")
        
        # 交互式配置
        providers = ['openai', 'anthropic', 'google', 'deepseek']
        
        for provider in providers:
            if click.confirm(f'配置 {provider}?'):
                api_key = click.prompt(f'{provider} API密鑰', hide_input=True)
                model = click.prompt(f'{provider} 模型名稱', 
                                   default=_get_default_model(provider))
                
                config.add_model_config(provider, ModelConfig(
                    provider=provider,
                    model=model,
                    api_key=api_key
                ))
        
        # 其他配置
        if click.confirm('配置驗證選項?'):
            config.validation.validate_instructions = click.confirm('驗證指令?', default=True)
            config.validation.validate_responses = click.confirm('驗證響應?', default=True)
            config.validation.strict_schema = click.confirm('嚴格Schema驗證?', default=True)
        
        if click.confirm('配置日誌選項?'):
            config.logging.level = click.prompt('日誌級別', 
                                              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
                                              default='INFO')
            config.logging.log_requests = click.confirm('記錄請求?', default=False)
            config.logging.log_responses = click.confirm('記錄響應?', default=False)
        
        # 保存配置
        config.save_to_file(output)
        
        console.print(f"[green]✅ 配置文件已保存到: {output}[/green]")
        
        # 顯示配置摘要
        table = Table(title="配置摘要")
        table.add_column("項目", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("配置的提供商", str(len(config.models)))
        table.add_row("驗證指令", str(config.validation.validate_instructions))
        table.add_row("驗證響應", str(config.validation.validate_responses))
        table.add_row("日誌級別", config.logging.level)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ 初始化配置失敗: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('--schema-file', '-s', type=click.Path(exists=True), required=True,
              help='JSON Schema文件路徑')
@click.option('--data-file', '-d', type=click.Path(exists=True), required=True,
              help='要驗證的JSON數據文件路徑')
def validate_schema(schema_file: str, data_file: str):
    """驗證JSON Schema"""
    try:
        from .validators import SchemaValidator
        
        # 加載Schema和數據
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        console.print("[yellow]驗證JSON Schema...[/yellow]")
        
        validator = SchemaValidator()
        
        try:
            is_valid = validator.validate(data, schema)
            if is_valid:
                console.print("[green]✅ 驗證通過！[/green]")
            else:
                console.print("[red]❌ 驗證失敗！[/red]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]❌ 驗證失敗: {e}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Schema驗證失敗: {e}[/red]")
        sys.exit(1)


def _get_default_model(provider: str) -> str:
    """獲取提供商的默認模型"""
    defaults = {
        'openai': 'gpt-4',
        'anthropic': 'claude-3-haiku-20240307',
        'google': 'gemini-pro',
        'deepseek': 'deepseek-chat'
    }
    return defaults.get(provider, 'unknown')


def _get_default_schema(instruction_type: str) -> Dict[str, Any]:
    """獲取指令類型的默認Schema"""
    schemas = {
        'structured_output': {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        },
        'text_analysis': {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["sentiment", "confidence"]
        },
        'extraction': {
            "type": "object",
            "properties": {
                "extracted_data": {"type": "object"}
            },
            "required": ["extracted_data"]
        },
        'generation': {
            "type": "object",
            "properties": {
                "generated_text": {"type": "string"}
            },
            "required": ["generated_text"]
        }
    }
    return schemas.get(instruction_type, schemas['structured_output'])


if __name__ == '__main__':
    main()