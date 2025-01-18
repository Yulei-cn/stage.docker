```markdown
Highlights of Technologies Used:
Google Cloud Platform: Google Cloud Run, Google Cloud SQL, Google Cloud Storage.
Docker: Containerized deployment for easy scalability and reproducibility.
Stripe: Payment gateway integration for secure and efficient transactions.
Ngrok: Tunneling for real-time development and testing.
Alibaba Cloud: Deployed services for multi-location scalability and reliability.


# 饮料点餐系统

这是一个基于Django开发的饮料点餐管理系统，旨在提高点餐效率并简化管理操作。

## 功能概览

### 1.0 版本
- 支持点餐和订单管理。
- 提供销售数据汇总页面。
- 包含现金收银员操作总结。
- 预定功能（隐藏）
- 二维码点单（隐藏）
- API连接外卖Uber eat和Deliveroo （沙盒测试成功）

### 2.0 版本
- **切换价格功能**：允许用户在不同价格模式之间进行切换。
- **自定义饮料功能**：支持用户根据需求添加和修改饮料配置。（未完成）
- **提交和打印按钮分开**:（bug 应该更细致区分第一次提交同时打印，而第二次提交则为更新，打印按钮始终独立）
- **更多统计数据分析**：运用正态分布计算最受欢迎的饮品对其进行促销活动

## 文件结构
- **views.py**: 处理业务逻辑。
- **models.py**: 定义数据库模型。
- **forms.py**: 提供表单功能支持。
- **templates/**: 包含所有HTML模板文件（如`base.html`, `cashier_summary.html`, `sales_overview.html`等）。
- **urls.py**: 路由配置。
- **settings.py**: 项目配置文件。

## 安装与运行

1. 克隆项目：
   ```bash
   git clone <repository_url>
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行迁移：
   ```bash
   python manage.py migrate
   ```
4. 启动开发服务器：
   ```bash
   python manage.py runserver
   ```

## 使用说明
- 登录系统后，管理员可访问自定义饮料页面，并根据需求新增或修改饮料选项。
- 在销售概览页面，可切换价格模式以便调整不同的价格配置。

## 贡献
欢迎提交Issue或Pull Request以改进项目。

## 许可
本项目采用MIT许可。
