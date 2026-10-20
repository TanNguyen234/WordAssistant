#!/usr/bin/env python3
"""Prepare and audit the StrongWine course essay without altering its source copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import sys
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lxml import etree
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DIAGRAM_ROOT = ROOT / "artifacts" / "strongwine-oop-essay" / "plantuml_overhaul"
SCREEN_HIERARCHY_NAMES = {"screen_hierarchy_customer", "screen_hierarchy_admin", "screen_hierarchy_shipper"}
SCHOOL = "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{" + NS["w"] + "}"
R = "{" + NS["r"] + "}"
DIAGRAM_CAPTIONS = {
    "class_architecture_layered": "Hình 3.1: Sơ đồ lớp kiến trúc phân tầng (Presentation - Service - Repository - Entity) của StrongWine",
    "erd_oop": "Hình 3.2: Mô hình miền cốt lõi StrongWine và enum Java hiện hành",
    "activity_shipment_otp": "Hình 3.19.c: Sơ đồ luồng xác thực và kiểm toán mã bảo mật giao hàng OTP",
    "screen_hierarchy_customer": "Hình 4.0: Sơ đồ phân rã màn hình phân hệ Khách hàng (Customer Screen Hierarchy Tree)",
    "usecase_customer": "Hình 4.0b: Sơ đồ Use Case chi tiết phân hệ Khách hàng",
    "activity_checkout": "Hình 4.4: Sơ đồ hoạt động (Activity Diagram) quy trình Checkout và thanh toán trực tuyến",
    "sequence_checkout": "Hình 4.5: Sơ đồ tuần tự (Sequence Diagram) xử lý Đặt hàng giữa các lớp ứng dụng",
    "screen_hierarchy_admin": "Hình 5.0: Sơ đồ phân rã màn hình phân hệ Quản trị và Thủ kho (Admin & Warehouse Screen Hierarchy Tree)",
    "usecase_admin": "Hình 5.0b: Sơ đồ Use Case chi tiết phân hệ Quản trị và Thủ kho",
    "activity_admin_create_wine": "Hình 5.1: Sơ đồ hoạt động (Activity Diagram) Quản trị viên thêm rượu và upload ảnh",
    "sequence_admin_create_wine": "Hình 5.2: Sơ đồ tuần tự Admin tạo rượu qua form MVC và FileStorageService",
    "screen_hierarchy_shipper": "Hình 6.0: Sơ đồ phân rã màn hình phân hệ Giao hàng (Shipper Cockpit Screen Hierarchy Tree)",
    "usecase_shipper": "Hình 6.0b: Sơ đồ Use Case chi tiết phân hệ Giao hàng (Shipper)",
}
PROJECT_MEDIA_CAPTIONS = {
    "Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_1_home.png",
    "Hình 4.5: Wireframe Giao diện thanh toán đơn hàng Checkout (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_5_checkout_v2.png",
    "Hình 4.6: Wireframe Chi tiết đơn hàng và theo dõi vận chuyển (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_6_order_detail.png",
    "Hình 4.2: Wireframe Danh mục rượu và bộ lọc đa tiêu chí (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_2_catalog.png",
    "Hình 4.2.b: Giao diện trang chủ StrongWine (ảnh giao diện từ bộ tài liệu dự án)":
    "docs/report-assets/desktop/customer-home.png",
    "Hình 4.3: Wireframe Chi tiết sản phẩm rượu và tasting notes (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_3_wine_detail.png",
    "Hình 4.7: Wireframe Đăng nhập và tạo tài khoản thành viên (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_7_auth.png",
    "Hình 4.8: Wireframe Biểu mẫu yêu cầu đặt lại mật khẩu bảo mật (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_8_password_reset.png",
    "Hình 4.4: Wireframe Quản lý giỏ hàng và cập nhật số lượng (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_4_4_cart.png",
    "Hình 4.9.b: Giao diện chi tiết đơn hàng và theo dõi giao nhận (ảnh giao diện từ bộ tài liệu dự án)":
    "docs/report-assets/desktop/customer-order-detail.jpg",
    "Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_3_admin_dashboard.png",
    "Hình 5.7: Wireframe Quản lý tài khoản người dùng và phân quyền (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_7_admin_users.png",
    "Hình 5.8: Wireframe Quản lý danh sách nhân viên giao hàng Shipper (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_8_admin_shippers.png",
    "Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_4_admin_wines_v2.png",
    "Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_5_admin_wine_form.png",
    "Hình 5.9: Wireframe Giám sát đơn hàng toàn sàn và trạng thái thanh toán (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_9_admin_orders.png",
    "Hình 5.10: Wireframe Bảng quản trị tồn kho và điều phối chi nhánh (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_10_admin_inventory.png",
    "Hình 5.6: Wireframe Nhập danh mục rượu hàng loạt từ tệp Excel (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_5_6_admin_excel_v2.png",
    "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper":
    "docs/report-assets/desktop/admin-shipper-edit.jpg",
    "Hình 6.1: Wireframe Bảng điều khiển công việc Shipper (Grayscale Web Mockup)":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_6_1_shipper_dashboard.png",
    "Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_6_2_shipper_delivery_detail_v2.png",
    "Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper":
    "artifacts/strongwine-oop-essay/wireframes_lowfi/wf_6_3_shipper_otp_v2.png",
}
PROJECT_MEDIA_CAPTION_ALIASES = {
    "Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper":
    ("Hình 6.2: Wireframe đề xuất chi tiết vận đơn và Google Maps Shipper (Grayscale Web Mockup)",),
    "Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper":
    ("Hình 6.3: Wireframe đề xuất màn hình OTP riêng cho Shipper (Grayscale Web Mockup)",),
}
PROJECT_MEDIA_FACTS = {
    "Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine (Grayscale Web Mockup)": {
        "route_paths": ["/home"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.5: Wireframe Giao diện thanh toán đơn hàng Checkout (Grayscale Web Mockup)": {
        "route_paths": ["/cart/checkout"], "payment_methods_supported": ["STRIPE"],
        "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.6: Wireframe Chi tiết đơn hàng và theo dõi vận chuyển (Grayscale Web Mockup)": {
        "route_paths": ["/orders/{id}"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.2: Wireframe Danh mục rượu và bộ lọc đa tiêu chí (Grayscale Web Mockup)": {
        "route_paths": ["/wines"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.2.b: Giao diện trang chủ StrongWine (ảnh giao diện từ bộ tài liệu dự án)": {
        "route_paths": ["/home"], "evidence_type": "saved project UI capture; exact source asset hash checked; fresh runtime capture NOT RUN",
        "runtime_verified": False
    },
    "Hình 4.3: Wireframe Chi tiết sản phẩm rượu và tasting notes (Grayscale Web Mockup)": {
        "route_paths": ["/wines/{id}"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.7: Wireframe Đăng nhập và tạo tài khoản thành viên (Grayscale Web Mockup)": {
        "route_paths": ["/login", "/register"], "note": "Two routes are shown in one composite wireframe.",
        "evidence_type": "source-backed composite wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.8: Wireframe Biểu mẫu yêu cầu đặt lại mật khẩu bảo mật (Grayscale Web Mockup)": {
        "route_paths": ["/forgot-password", "/reset-password"], "evidence_type": "source-backed composite wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.4: Wireframe Quản lý giỏ hàng và cập nhật số lượng (Grayscale Web Mockup)": {
        "route_paths": ["/cart"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 4.9.b: Giao diện chi tiết đơn hàng và theo dõi giao nhận (ảnh giao diện từ bộ tài liệu dự án)": {
        "route_paths": ["/orders/{id}"], "evidence_type": "saved project UI capture; exact source asset hash checked; fresh runtime capture NOT RUN",
        "runtime_verified": False
    },
    "Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI (Grayscale Web Mockup)": {
        "route_paths": ["/admin"], "evidence_type": "source-backed wireframe; panels show structure, not metrics", "sample_data": False
    },
    "Hình 5.7: Wireframe Quản lý tài khoản người dùng và phân quyền (Grayscale Web Mockup)": {
        "route_paths": ["/admin/users"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 5.8: Wireframe Quản lý danh sách nhân viên giao hàng Shipper (Grayscale Web Mockup)": {
        "route_paths": ["/admin/shippers"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang (Grayscale Web Mockup)": {
        "route_paths": ["/wines"], "note": "Admin actions may be role-dependent on the catalog view; there is no /admin/wines list route.",
        "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu (Grayscale Web Mockup)": {
        "route_paths": ["/wines/admin/create", "/wines/admin/edit/{id}"], "evidence_type": "source-backed composite form state; not a runtime screenshot", "sample_data": False
    },
    "Hình 5.9: Wireframe Giám sát đơn hàng toàn sàn và trạng thái thanh toán (Grayscale Web Mockup)": {
        "route_paths": ["/admin/orders"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 5.10: Wireframe Bảng quản trị tồn kho và điều phối chi nhánh (Grayscale Web Mockup)": {
        "route_paths": ["/admin/inventory"], "evidence_type": "source-backed wireframe; not a runtime screenshot", "sample_data": False
    },
    "Hình 5.6: Wireframe Nhập danh mục rượu hàng loạt từ tệp Excel (Grayscale Web Mockup)": {
        "route_paths": ["/admin/wines/import"], "evidence_type": "source-backed wireframe; blank preview rows", "sample_data": False
    },
    "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper": {
        "route_paths": ["/admin/shippers/edit/{id}"], "evidence_type": "saved project UI capture; exact source asset hash checked; fresh runtime capture NOT RUN",
        "runtime_verified": False
    },
    "Hình 6.1: Wireframe Bảng điều khiển công việc Shipper (Grayscale Web Mockup)": {
        "route_paths": ["/shipper", "/shipper/dashboard", "/shipper/shipments"], "evidence_type": "source-backed wireframe; route aliases share one dashboard", "sample_data": False
    },
    "Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper": {
        "route_paths": ["/shipper/dashboard"], "implementation_status": "Inline state in the single shipper dashboard, not a separate page.",
        "evidence_type": "source-backed dashboard state; not a runtime screenshot", "sample_data": False
    },
    "Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper": {
        "route_paths": ["/shipper/dashboard"], "implementation_status": "OTP inputs are embedded in the dashboard card; completion submits POST /shipper/shipments/{id}/complete.",
        "evidence_type": "source-backed dashboard state; not a runtime screenshot", "sample_data": False
    },
}
PROJECT_MEDIA_EXPECTED_SHA256 = {
    'Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine (Grayscale Web Mockup)': 'e2769ecc980602643b09e14095ae4be41bf28da46505c28744928ce2415dfa69',
    'Hình 4.5: Wireframe Giao diện thanh toán đơn hàng Checkout (Grayscale Web Mockup)': 'd10761311b9eab51651333fed623a245b059a99b3cc50b75dab8401cdd9b5ab0',
    'Hình 4.6: Wireframe Chi tiết đơn hàng và theo dõi vận chuyển (Grayscale Web Mockup)': '0d2adafb89c10c9ff22606a217a6ac64386fb3269ad6bf15692ebb8f6edad5d1',
    'Hình 4.2: Wireframe Danh mục rượu và bộ lọc đa tiêu chí (Grayscale Web Mockup)': '583c9fca210dc070a4dcc5a76a6d4f410200a45886f66eed96dc26b2e8fba490',
    'Hình 4.2.b: Giao diện trang chủ StrongWine (ảnh giao diện từ bộ tài liệu dự án)': '906df587fb6a8f356121287b645def155045299269da8683dfb70cd6e526ca21',
    'Hình 4.3: Wireframe Chi tiết sản phẩm rượu và tasting notes (Grayscale Web Mockup)': 'd44c66c5afca17054ab96c4b3f9ce75b87d69af2ad4f2f7a6bdf3733d9f4697a',
    'Hình 4.7: Wireframe Đăng nhập và tạo tài khoản thành viên (Grayscale Web Mockup)': 'c6afab82656682b39c02edd8068b0a60a66e8e6b06887088c35bdbd4a5c61f8b',
    'Hình 4.8: Wireframe Biểu mẫu yêu cầu đặt lại mật khẩu bảo mật (Grayscale Web Mockup)': '32cd6015891baa53aebf39d0e379c4ef8d58a8cb8d826830e3f87fc875d2682f',
    'Hình 4.4: Wireframe Quản lý giỏ hàng và cập nhật số lượng (Grayscale Web Mockup)': 'c9cd0426048e32ffee47a2d558b70b0ad21f63c57ec77a2519508b61d8915af4',
    'Hình 4.9.b: Giao diện chi tiết đơn hàng và theo dõi giao nhận (ảnh giao diện từ bộ tài liệu dự án)': '37336d5b9e7b0ddb984202066350a359c32dbe1831c1ae4925277d54c6ca336a',
    'Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI (Grayscale Web Mockup)': 'c60b9d575a5ad88fac7e307ed20fd1e12ead70987561b8337ec835292661565c',
    'Hình 5.7: Wireframe Quản lý tài khoản người dùng và phân quyền (Grayscale Web Mockup)': '1c371855f7078f90653b322f9db9b5ac8ab382f1ddeadbb6beee6260a722c35f',
    'Hình 5.8: Wireframe Quản lý danh sách nhân viên giao hàng Shipper (Grayscale Web Mockup)': '24df08a441ea5c5d434c9f9de848bd61e3e1331465b6d3b22f77a3d9296e325f',
    'Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang (Grayscale Web Mockup)': '1c57b91bd1f24f1672709724e1e77a7a5b5a6fb23e631d6b2c824b7111f802f0',
    'Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu (Grayscale Web Mockup)': '447da7038ce71ac5f1e8f29d2fd99d7d35996e76d8d2d8a0189303c5795240ec',
    'Hình 5.9: Wireframe Giám sát đơn hàng toàn sàn và trạng thái thanh toán (Grayscale Web Mockup)': '7eef0077a0f077cecf96469ed7f0c58e93a3de75a324296995108a368aadad39',
    'Hình 5.10: Wireframe Bảng quản trị tồn kho và điều phối chi nhánh (Grayscale Web Mockup)': 'aa42ebbd31c9327b6f9369e3995d0d16d655e60614dc9ffd5340ac842da911f4',
    'Hình 5.6: Wireframe Nhập danh mục rượu hàng loạt từ tệp Excel (Grayscale Web Mockup)': '53c193ac3611933bc362990c58979052c74c99b56869b6dbe768afe695c7f288',
    'Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper': '0170da451c6c6043a1e32b223ecd7dc6530bab948c2e96952fbd512280f4c1ca',
    'Hình 6.1: Wireframe Bảng điều khiển công việc Shipper (Grayscale Web Mockup)': '815a9b321af60e692155abb6003f667bea3d9a05810d5ab9077371357df0b803',
    'Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper': '3bea0f34d8818c314dac3b87e48eef03ccb3738abd0cf4f4985cce160b8f1e05',
    'Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper': '3529aae6b4f4f880a8ac4c1bd92624e0ecbfde2e432064b43d4c2e73bc3866db',
}
PROJECT_ROUTE_ASSERTIONS = {
    "/home": ("HomeController.java", ('@GetMapping("/home")',)),
    "/wines": ("WineController.java", ('@RequestMapping("/wines")', "@GetMapping")),
    "/wines/{id}": ("WineController.java", ('@RequestMapping("/wines")', '@GetMapping("/{id}")')),
    "/wines/admin/create": ("WineController.java", ('@RequestMapping("/wines")', '@GetMapping("/admin/create")')),
    "/cart": ("CartController.java", ('@RequestMapping("/cart")', "@GetMapping")),
    "/cart/checkout": ("CartController.java", ('@RequestMapping("/cart")', '@GetMapping("/checkout")')),
    "/orders/{id}": ("OrderController.java", ('@GetMapping("/orders/{id}")',)),
    "/orders": ("OrderController.java", ('@GetMapping("/orders")',)),
    "/order-confirmation": ("OrderController.java", ('@GetMapping("/order-confirmation")',)),
    "/login": ("AuthController.java", ('@GetMapping("/login")',)),
    "/register": ("AuthController.java", ('@GetMapping("/register")',)),
    "/forgot-password": ("AuthController.java", ('@GetMapping("/forgot-password")',)),
    "/reset-password": ("AuthController.java", ('@GetMapping("/reset-password")',)),
    "/admin": ("AdminController.java", ('@RequestMapping("/admin")', "@GetMapping")),
    "/admin/users": ("AdminUserController.java", ('@RequestMapping("/admin/users")', "@GetMapping")),
    "/admin/users/create": ("AdminUserController.java", ('@RequestMapping("/admin/users")', '@GetMapping("/create")')),
    "/admin/users/edit/{id}": ("AdminUserController.java", ('@RequestMapping("/admin/users")', '@GetMapping("/edit/{id}")')),
    "/admin/shippers": ("AdminShipperController.java", ('@RequestMapping("/admin/shippers")', "@GetMapping")),
    "/admin/shippers/create": ("AdminShipperController.java", ('@RequestMapping("/admin/shippers")', '@GetMapping("/create")')),
    "/admin/shippers/edit/{id}": ("AdminShipperController.java", ('@RequestMapping("/admin/shippers")', '@GetMapping("/edit/{id}")')),
    "/admin/orders": ("AdminOrderController.java", ('@RequestMapping("/admin/orders")', "@GetMapping")),
    "/admin/payments": ("AdminPaymentController.java", ('@RequestMapping("/admin/payments")', "@GetMapping")),
    "/admin/shipments": ("AdminShipmentController.java", ('@RequestMapping("/admin/shipments")', "@GetMapping")),
    "/admin/shipments/edit/{id}": ("AdminShipmentController.java", ('@RequestMapping("/admin/shipments")', '@GetMapping("/edit/{id}")')),
    "/admin/inventory": ("AdminInventoryController.java", ('@RequestMapping("/admin/inventory")', "@org.springframework.web.bind.annotation.GetMapping")),
    "/admin/wines/import": ("AdminController.java", ('@RequestMapping("/admin")', '@GetMapping("/wines/import")')),
    "/wines/admin/edit/{id}": ("WineController.java", ('@RequestMapping("/wines")', '@GetMapping("/admin/edit/{id}")')),
    "/shipper": ("ShipperController.java", ('@RequestMapping("/shipper")', '@GetMapping({"", "/dashboard", "/shipments"})')),
    "/shipper/dashboard": ("ShipperController.java", ('@RequestMapping("/shipper")', '@GetMapping({"", "/dashboard", "/shipments"})')),
    "/shipper/shipments": ("ShipperController.java", ('@RequestMapping("/shipper")', '@GetMapping({"", "/dashboard", "/shipments"})')),
}
MISLEADING_FIGURE_RULES = {
    "Hình 4.5.b: Giao diện thực tế quy trình thanh toán đơn hàng Checkout (Ảnh chụp màn hình web)": {
        "source": "docs/report-assets/desktop/customer-checkout.jpg",
        "expected_sha256": "a223b269d3106d3b0b5f47337a69ba90b953b98efb4ac4014c3e220d1cddd729",
        "reason": "The image is an empty /cart screenshot, not the /cart/checkout page named by the caption.",
    },
    "Hình 5.9.b: Wireframe Chỉnh sửa hồ sơ người giao hàng Shipper (Grayscale Web Mockup)": {
        "source": "docs/report-assets/diagrams_v2/hinh_6_0_shipper_sitemap.png",
        "expected_sha256": "dd5a60dffbe69c10de2c3f44b6be4bb267aa282f200f20449c84e412870e4583",
        "reason": "The image is a Shipper screen hierarchy diagram, not an edit-shipper wireframe; the correct edit interface is shown in Hình 5.10.",
    },
}
SUPERSEDED_SCREEN_ASSETS = {
    "docs/report-assets/wireframes_grayscale/wf_4_5_checkout.png": {
        "expected_sha256": "649157841af9574007fa0374fb017672a97c1bc93811049f7ee8ce899f48268d",
        "reason": "Wrong /checkout route and unsupported VietQR/COD payment choices; use wf_4_5_checkout_v2.png.",
    },
    "docs/report-assets/wireframes_grayscale/wf_5_4_admin_wines.png": {
        "expected_sha256": "e49164a8d5121fdb125041cf7acd2eaff2e9fab4a38e0ab2b3d294d2da16ceaf",
        "reason": "Uses non-existent /admin/wines route; use wf_5_4_admin_wines_v2.png.",
    },
    "docs/report-assets/wireframes_grayscale/wf_5_6_admin_excel.png": {
        "expected_sha256": "23c9d20fd0bf289362439381129cdb964ef02644ab445208b3a7f68c34a2f8e5",
        "reason": "Uses non-existent /admin/wines/import-excel route; use wf_5_6_admin_excel_v2.png.",
    },
    "docs/report-assets/wireframes_grayscale/wf_6_2_shipper_delivery_detail.png": {
        "expected_sha256": "d54a22153e9e1100feba3c2dbae7ef8a0b9cc0836410711bd099e91208d880d4",
        "reason": "Uses non-existent /shipper/deliveries/{id} page; use the dashboard-state proposal v2.",
    },
    "docs/report-assets/wireframes_grayscale/wf_6_3_shipper_otp.png": {
        "expected_sha256": "6f6aaf99b3be20bda9717a95fec5d0e0547e7099bb0d339d6412f91352115340",
        "reason": "Uses non-existent standalone verify-otp route; use the dashboard-state proposal v2.",
    },
}
ENUMS = (
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "ShipperStatus",
    "ShipmentStatus",
    "InventoryOperationType",
)
REQUIRED_DIAGRAM_TEXT = {
    "class_architecture_layered": ("CartController", "OrderService", "InventoryService", "FileStorageService"),
    "erd_oop": ("OrderStatus", "PaymentStatus", "PaymentMethod", "ShipmentStatus"),
    "screen_hierarchy_customer": ("MVC GET", "Danh mục rượu", "Checkout", "Đăng nhập", "Đăng ký", "Đơn hàng của tôi"),
    "screen_hierarchy_admin": ("MVC GET", "Đơn hàng toàn sàn", "Thanh toán", "Tồn kho", "Tạo người dùng", "Sửa vận đơn"),
    "screen_hierarchy_shipper": ("MVC GET", "Bảng điều khiển giao hàng"),
    "usecase_customer": ("STRIPE", "Thanh toán checkout"),
    "usecase_admin": ("Quản lý đơn hàng", "Quản lý tồn kho / Excel"),
    "usecase_shipper": ("Hoàn tất giao với OTP", "Báo giao thất bại"),
    "activity_checkout": ("POST /cart/checkout/process", "Stripe-Signature", "OrderPaidEvent"),
    "sequence_checkout": ("POST /cart/checkout/process", "POST /payment/webhook", "AFTER_COMMIT"),
    "activity_admin_create_wine": ("/wines/admin/create", "JPG/JPEG/PNG", "WineService.createWine"),
    "sequence_admin_create_wine": ("/wines/admin/create", "FileStorageService", "WineRepository"),
    "activity_shipment_otp": ("/shipper/shipments/{id}/complete?otp=...", "COMPLETED"),
    "sequence_payment_webhook": ("POST /payment/webhook", "Stripe-Signature", "AFTER_COMMIT"),
}
FORBIDDEN_DIAGRAM_TEXT = {
    "class_architecture_layered": ("OrderController", "ServiceImpl", "/api/admin/wines"),
    "erd_oop": ("IN_TRANSIT", "DELIVERED", "FAILED_ATTEMPT", "IMPORT_EXCEL", "MANUAL_ADJUST"),
    "screen_hierarchy_customer": ("POST ", "Stripe Checkout", "VNPAY", "COD", "JWT"),
    "screen_hierarchy_admin": ("POST ", "CONFIRMED", "AVAILABLE", "VNPAY"),
    "screen_hierarchy_shipper": ("POST ", "IN_TRANSIT", "DELIVERED", "FAILED_ATTEMPT", "RETURNED", "COD"),
    "usecase_customer": ("VNPAY", "COD", "JWT"),
    "usecase_shipper": ("IN_TRANSIT", "DELIVERED", "FAILED_ATTEMPT", "RETURNED", "COD"),
    "activity_checkout": ("VNPAY", "COD", "OrderController", "CONFIRMED"),
    "sequence_checkout": ("/orders/checkout", "OrderController", "VNPAY", "COD"),
    "activity_admin_create_wine": ("/api/admin/wines", "AdminProductApiController", "WEBP", "INITIAL_IMPORT"),
    "sequence_admin_create_wine": ("/api/admin/wines", "AdminProductApiController", "WEBP"),
    "activity_shipment_otp": ("IN_TRANSIT", "DELIVERED", "FAILED_ATTEMPT", "RETURNED"),
    "sequence_payment_webhook": ("VNPAY", "/api/payments/webhook", "CONFIRMED"),
}
VERIFIED_TEXT_EDITS = {
    "Thông tin về Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh và Khoa Công nghệ Thông tin được đối chiếu với tài liệu cũ do em cung cấp. Tài liệu đó chỉ được dùng để xác định thông tin trường, khoa và tham khảo một số sơ đồ được chú thích rõ; ảnh giao diện cũ không được đưa vào thay ảnh hiện hành. Ảnh trong bài được chụp từ ứng dụng đang chạy cho các vai trò khách hàng, quản trị viên và shipper trong môi trường khảo sát.":
    "Thông tin về Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh và Khoa Công nghệ Thông tin được đối chiếu với tài liệu do sinh viên cung cấp. Hình trong bài gồm wireframe được dựng từ các MVC GET view và template đã kiểm tra, cùng một số ảnh giao diện có sẵn trong bộ tài liệu dự án. Các ảnh có sẵn chưa được chụp lại từ runtime trong lượt hiệu đính này.",
    "Hình 4.2.b: Giao diện thực tế Trang chủ và Danh mục rượu (Ảnh chụp màn hình web)":
    "Hình 4.2.b: Giao diện trang chủ StrongWine (ảnh giao diện từ bộ tài liệu dự án)",
    "Hình 4.9.b: Giao diện thực tế Lịch sử đơn hàng và Chi tiết giao nhận (Ảnh chụp màn hình web)":
    "Hình 4.9.b: Giao diện chi tiết đơn hàng và theo dõi giao nhận (ảnh giao diện từ bộ tài liệu dự án)",
    "Hình 5.10: Chỉnh sửa hồ sơ người giao hàng":
    "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper",
    "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper (ảnh giao diện từ bộ tài liệu dự án)":
    "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper",
    "Hình 6.2: Wireframe đề xuất chi tiết vận đơn và Google Maps Shipper (Grayscale Web Mockup)":
    "Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper",
    "Hình 6.3: Wireframe đề xuất màn hình OTP riêng cho Shipper (Grayscale Web Mockup)":
    "Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper",
    "Sơ đồ Lớp Thực thể ORM (JPA/OOP Domain Entity Model) bên dưới biểu diễn toàn bộ mô hình dữ liệu hướng đối tượng của hệ thống StrongWine. Toàn bộ các thực thể (Wine, Category, Order, OrderItem, Payment, Shipment, Shipper, Inventory, Warehouse, StockLog, Cart, Review) đều được mô hình hóa theo đúng quan hệ OOP chặt chẽ (Composition, Aggregation, Kế thừa Auditable, Quan hệ 1-N, N-N) và tích hợp các Enum trạng thái nghiệp vụ chuẩn xác.":
    "Sơ đồ miền bên dưới trình bày tập entity cốt lõi gồm User, Category, Wine, Warehouse, Inventory, Order, OrderItem, Payment, Shipment, Shipper và PaymentTransaction, cùng các quan hệ JPA được khảo sát. Đây không phải toàn bộ entity graph; các enum được liệt kê theo literal Java hiện hành. Quan hệ composition chỉ dùng ở những cặp có vòng đời thành phần phù hợp.",
    "Hình 3.2: Sơ đồ Lớp Thực thể ORM (JPA/OOP Domain Entity Model) của StrongWine":
    "Hình 3.2: Mô hình miền cốt lõi StrongWine và enum Java hiện hành",
    "Sơ đồ cây phân cấp màn hình phân hệ Khách hàng dưới đây mô tả cấu trúc liên kết toàn diện giữa các màn hình từ Trang chủ, Khám phá danh mục, Chi tiết rượu nếm thử, Giỏ hàng, Đặt hàng Checkout, Cổng thanh toán, Lịch sử đơn và Đánh giá.":
    "Sơ đồ cây màn hình khách hàng tổng hợp các MVC GET view đã kiểm tra: trang chủ; danh mục và chi tiết rượu; giỏ hàng và checkout; đăng nhập, đăng ký, quên mật khẩu và đặt lại mật khẩu; danh sách, chi tiết và xác nhận đơn hàng. Đặt hàng gửi POST /cart/checkout/process; luồng checkout hiện chuyển khách tới Stripe Checkout.",
    "Sơ đồ hoạt động quy trình Checkout và thanh toán bên dưới thể hiện rõ ràng luồng đặt hàng trực tuyến từ giỏ hàng: kiểm tra tồn kho khả dụng, tạm khóa số lượng tồn (Reserve Quantity), lựa chọn phương thức thanh toán (COD hoặc VNPAY/Stripe), xử lý webhook bất đồng bộ, xác nhận đơn hàng và kích hoạt tiến trình tạo vận đơn giao hàng tự động.":
    "Sơ đồ hoạt động checkout bám theo POST /cart/checkout/process: CartController kiểm tra phiên và dữ liệu, OrderService tạo đơn PENDING và giữ tồn, PaymentService mở Stripe Checkout. Webhook Stripe hợp lệ cập nhật Payment SUCCESS/Order PAID; listener xử lý shipment sau commit.",
    "Sơ đồ tuần tự tương tác lớp khi Checkout và Đặt hàng mô tả chi tiết thứ tự lời gọi hàm giữa OrderController, OrderService, InventoryService, PaymentService và OrderRepository. Mọi tương tác đều tuân thủ nguyên lý Dependency Injection, giao dịch dữ liệu nhất quán (@Transactional) và kích hoạt sự kiện nội bộ OrderCreatedEvent qua ApplicationEventPublisher.":
    "Sơ đồ tuần tự thể hiện POST /cart/checkout/process qua CartController, OrderService, InventoryService, PaymentService và Stripe; POST /payment/webhook xử lý xác nhận. Khi OrderPaidEvent được phát, OrderPaidShipmentListener gọi xử lý shipment ở pha AFTER_COMMIT.",
    "Sơ đồ ca sử dụng phân hệ Quản trị viên và Thủ kho mô tả chi tiết quyền hạn quản trị đơn hàng, duyệt thanh toán, thiết lập mức cảnh báo tồn kho và chạy nghiệm ngặt tệp Excel.":
    "Sơ đồ use case nhóm các khu vực controller quản trị hiện có: dashboard, rượu, đơn hàng, thanh toán, tồn kho/Excel, tài khoản người dùng, hồ sơ shipper và vận đơn. Từng quyền thao tác cần được xác nhận tại endpoint tương ứng.",
    "Quy trình thêm mới sản phẩm rượu vang vào hệ thống bao gồm các bước kiểm tra tính hợp lệ của dữ liệu biểu mẫu, xử lý tập tin hình ảnh và lưu trữ đồng thời vào kho dữ liệu. Sơ đồ hoạt động mô tả chi tiết các bước xử lý nghiệp vụ của quản trị viên như sau:":
    "Form MVC tạo rượu kiểm tra dữ liệu, nhận file ảnh tùy chọn hoặc URL, lưu file hợp lệ qua FileStorageService và gọi WineService. Luồng này không tự khởi tạo tồn kho trong phương thức WineController đang khảo sát.",
    "Sơ đồ tuần tự bên dưới ghi cụ thể `/admin/wines/create` và FileStorageService. Route, lớp lưu ảnh và giới hạn dung lượng cần kiểm tra theo mã hiện hành trước khi tái sử dụng sơ đồ này.":
    "Sơ đồ tuần tự đã đối chiếu với form MVC GET/POST /wines/admin/create. API /api/admin/products là giao diện JSON riêng, không nhận MultipartFile trong luồng tạo rượu này.",
    "Hình 5.2: Sơ đồ tuần tự (Sequence Diagram) Admin thêm rượu và lưu ảnh qua FileStorageService":
    "Hình 5.2: Sơ đồ tuần tự Admin tạo rượu qua form MVC và FileStorageService",
    "Giao diện đăng ký tài khoản thành viên mới thu thập thông tin cá nhân và thiết lập mật mã an toàn:":
    "Wireframe dưới đây minh họa form MVC tạo rượu tại GET/POST /wines/admin/create; file ảnh hỗ trợ JPG/JPEG/PNG, tối đa 5 MB. Giá trị trong form là ví dụ; đây không phải ảnh chụp runtime.",
    "Màn hình yêu cầu cấp lại mật khẩu hỗ trợ gửi mã token xác thực an toàn qua hòm thư điện tử:":
    "Sơ đồ cây kế tiếp tổng hợp các khu vực và route quản trị hiện có; route tạo rượu đã đối chiếu với WineController.",
    "Sơ đồ cây phân cấp màn hình phân hệ Giao hàng (Shipper Cockpit) phân rã 3 nhóm tác vụ trọng tâm trên giao diện thiết bị di động: Nhận đơn & bản đồ chỉ đường GPS; Quy trình phát hàng & xác thực mã OTP bảo mật hai chiều; cùng Báo cáo giao nhận, quyết toán COD và nhận thông báo thời gian thực SSE.":
    "Controller shipper trả một view dashboard cho GET /shipper, /shipper/dashboard và /shipper/shipments. Trên dashboard, shipper xem shipment của mình và gửi các POST lấy hàng, bắt đầu giao, hoàn tất bằng OTP, gửi lại OTP hoặc báo thất bại.",
    "Sơ đồ ca sử dụng phân hệ Shipper mô tả chi tiết quyền hạn tiếp nhận đơn, cập nhật trạng thái di chuyển, đối soát thu tiền mặt COD và lắng nghe thông báo đơn mới qua Server-Sent Events (SSE).":
    "Use case shipper giới hạn ở các hành động controller hiện có: xem shipment được giao, xác nhận lấy hàng, bắt đầu giao, hoàn tất với OTP, yêu cầu gửi lại OTP và báo giao thất bại.",
    "Khu vực shipper được tổ chức ưu tiên màn hình điện thoại, vì nhân viên giao hàng cần xem danh sách việc và xác nhận trạng thái tại hiện trường. Giao diện hiển thị thẻ thống kê theo nhóm trạng thái và hành động gắn với từng vận đơn.":
    "Controller hiện trả cùng một view dashboard và gắn danh sách shipment theo tài khoản. Các thao tác POST đều quay lại dashboard; controller này không khai báo view chi tiết hoặc danh sách vận đơn riêng.",
    "Tại địa điểm giao hàng, Shipper yêu cầu người nhận cung cấp mã 6 chữ số và nhập vào màn hình giao vận `/shipper/shipments/{id}/complete`. Hệ thống tiếp nhận mã, chuẩn hóa chuỗi dữ liệu, kiểm tra thời hạn hiệu lực và so sánh đối chiếu với giá trị trong cơ sở dữ liệu. Mỗi lần nhập sai, biến đếm số lần thử được tăng tự động; nếu nhập sai quá 5 lần liên tiếp, vận đơn bị khóa xác thực trong vòng 15 phút để phòng chống tấn công dò mã kiểu Brute-force. Khi mã OTP hoàn toàn trùng khớp, hệ thống cập nhật trạng thái vận đơn thành `DELIVERED`, đơn hàng tương ứng chuyển sang `COMPLETED`, ghi nhận dấu thời gian hoàn thành và cập nhật công nợ cho shipper trong cùng một transaction toàn vẹn.":
    "Tại điểm giao, Shipper gửi OTP qua POST /shipper/shipments/{id}/complete. ShipmentService xác nhận shipper được giao shipment, trạng thái hiện tại là DELIVERING, mã đủ 6 chữ số, còn hạn và chưa bị khóa. Mã sai làm tăng bộ đếm và được ghi audit; khi đạt ngưỡng cấu hình, xác thực bị khóa tạm thời. Mã đúng chuyển Shipment sang COMPLETED, đặt otpVerified, xóa dữ liệu OTP nhạy cảm và ghi lịch sử trạng thái. Luồng này không đổi Order sang DELIVERED hoặc cập nhật công nợ COD.",
}
VERIFIED_TEXT_EDIT_ALIASES = {
    "Sơ đồ cây phân cấp màn hình phân hệ Khách hàng dưới đây mô tả cấu trúc liên kết toàn diện giữa các màn hình từ Trang chủ, Khám phá danh mục, Chi tiết rượu nếm thử, Giỏ hàng, Đặt hàng Checkout, Cổng thanh toán, Lịch sử đơn và Đánh giá.": (
        "Sơ đồ cây màn hình khách hàng tổng hợp các MVC route đã kiểm tra: trang chủ, danh mục và chi tiết rượu, giỏ hàng, checkout, đăng nhập/đăng ký và đơn hàng. Đặt hàng gửi POST /cart/checkout/process; luồng checkout hiện chuyển khách tới Stripe Checkout.",
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_project_asset(project_root: Path, relative_path: str) -> Path:
    """Resolve source screenshots from the project and generated wireframes from this workspace."""
    candidate = project_root / Path(relative_path)
    if candidate.is_file():
        return candidate
    workspace_candidate = ROOT / Path(relative_path)
    if relative_path.replace("\\", "/").startswith("artifacts/") and workspace_candidate.is_file():
        return workspace_candidate
    return candidate


def xml_bytes(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def cover_ranges(paragraphs: list[etree._Element]) -> list[tuple[int, int]]:
    texts = ["".join(p.xpath(".//w:t/text()", namespaces=NS)).strip() for p in paragraphs]
    anchors = [i for i, text in enumerate(texts) if text == SCHOOL]
    if len(anchors) != 2:
        raise ValueError(f"Expected exactly two cover anchors, found {len(anchors)}")
    ranges: list[tuple[int, int]] = []
    for anchor in anchors:
        end = next(
            (i for i in range(anchor, len(texts)) if texts[i].startswith("TP. Hồ Chí Minh, tháng ")),
            None,
        )
        if end is None:
            raise ValueError(f"Could not find the cover date after paragraph {anchor}")
        ranges.append((anchor, end))
    if ranges[0][1] >= ranges[1][0]:
        raise ValueError("Cover blocks overlap or appear in an unexpected order")
    return ranges


def center_paragraph(paragraph: etree._Element) -> None:
    ppr = paragraph.find(W + "pPr")
    if ppr is None:
        ppr = etree.Element(W + "pPr")
        paragraph.insert(0, ppr)
    jc = ppr.find(W + "jc")
    if jc is None:
        jc = etree.SubElement(ppr, W + "jc")
    jc.set(W + "val", "center")


def paragraph_style_alignments(styles_xml: bytes) -> dict[str, tuple[str | None, str | None]]:
    styles = etree.fromstring(styles_xml)
    result = {}
    for style in styles.xpath("./w:style", namespaces=NS):
        style_id = style.get(W + "styleId")
        align = style.find("w:pPr/w:jc", NS)
        parent = style.find("w:basedOn", NS)
        if style_id:
            result[style_id] = (align.get(W + "val") if align is not None else None,
                                parent.get(W + "val") if parent is not None else None)
    return result


def paragraph_is_centered(paragraph: etree._Element, styles: dict[str, tuple[str | None, str | None]]) -> bool:
    ppr = paragraph.find(W + "pPr")
    direct = ppr.find(W + "jc") if ppr is not None else None
    if direct is not None:
        return direct.get(W + "val") == "center"
    style_ref = ppr.find(W + "pStyle") if ppr is not None else None
    style_id = style_ref.get(W + "val") if style_ref is not None else None
    visited = set()
    while style_id and style_id not in visited:
        visited.add(style_id)
        align, parent = styles.get(style_id, (None, None))
        if align is not None:
            return align == "center"
        style_id = parent
    return False


def set_page_border(section: etree._Element, display: str) -> None:
    old = section.find(W + "pgBorders")
    if old is not None:
        section.remove(old)
    borders = etree.Element(W + "pgBorders")
    # Word treats a page-relative border as a narrow line beside the paper edge,
    # regardless of a large `space` value. Text-relative borders follow the
    # document margins and remain visibly inset after Word saves the DOCX.
    borders.set(W + "offsetFrom", "text")
    borders.set(W + "display", display)
    for edge in ("top", "left", "bottom", "right"):
        node = etree.SubElement(borders, W + edge)
        node.set(W + "val", "double")
        node.set(W + "sz", "8")
        node.set(W + "space", "4")
        node.set(W + "color", "000000")
    page_margins = section.find(W + "pgMar")
    if page_margins is not None:
        # Word positions the top/bottom frame beside the header/footer area.
        # Increase those offsets slightly so the rendered frame clears 12 mm.
        for edge in ("header", "footer"):
            current = int(page_margins.get(W + edge, "0"))
            page_margins.set(W + edge, str(max(current, 900)))
    insert_at = list(section).index(page_margins) + 1 if page_margins is not None else len(section)
    section.insert(insert_at, borders)


def set_vertical_alignment(section: etree._Element, alignment: str | None) -> None:
    vertical = section.find(W + "vAlign")
    if vertical is not None:
        section.remove(vertical)
    if alignment is None:
        return
    vertical = etree.Element(W + "vAlign")
    vertical.set(W + "val", alignment)
    title_page = section.find(W + "titlePg")
    insert_at = list(section).index(title_page) if title_page is not None else len(section)
    section.insert(insert_at, vertical)


def split_inner_cover_section(paragraph: etree._Element, continuation_section: etree._Element) -> etree._Element:
    """Give the second cover its own page section while preserving following-page settings."""
    if paragraph.find("./w:pPr/w:sectPr", NS) is not None:
        raise ValueError("The inner-cover end paragraph already owns a section break")

    cover_section = etree.fromstring(etree.tostring(continuation_section))
    section_type = cover_section.find(W + "type")
    if section_type is None:
        section_type = etree.Element(W + "type")
        reference_names = {W + "headerReference", W + "footerReference", W + "footnotePr", W + "endnotePr"}
        reference_indices = [index for index, item in enumerate(cover_section) if item.tag in reference_names]
        cover_section.insert(max(reference_indices) + 1 if reference_indices else 0, section_type)
    section_type.set(W + "val", "nextPage")

    paragraph_properties = paragraph.find(W + "pPr")
    if paragraph_properties is None:
        paragraph_properties = etree.Element(W + "pPr")
        paragraph.insert(0, paragraph_properties)
    paragraph_properties.append(cover_section)

    # The original section continues with acknowledgments and front matter.
    # Keep its regular header/footer and page geometry, but remove cover-only behavior.
    border = continuation_section.find(W + "pgBorders")
    if border is not None:
        continuation_section.remove(border)
    title_page = continuation_section.find(W + "titlePg")
    if title_page is not None:
        continuation_section.remove(title_page)
    set_vertical_alignment(continuation_section, None)
    page_numbering = continuation_section.find(W + "pgNumType")
    if page_numbering is not None and page_numbering.get(W + "start") is not None:
        page_numbering.attrib.pop(W + "start", None)
        if not page_numbering.attrib:
            continuation_section.remove(page_numbering)

    set_page_border(cover_section, "allPages")
    set_vertical_alignment(cover_section, "center")
    return cover_section


def add_first_page_reference(section: etree._Element, kind: str, relationship_id: str) -> None:
    tag = W + kind + "Reference"
    reference = next((item for item in section.findall(tag) if item.get(W + "type") == "first"), None)
    if reference is None:
        reference = etree.Element(tag)
        reference.set(W + "type", "first")
        if kind == "header":
            existing = section.findall(W + "headerReference")
            if existing:
                section.insert(list(section).index(existing[-1]) + 1, reference)
            else:
                section.insert(0, reference)
        else:
            existing = section.findall(W + "footerReference")
            if existing:
                section.insert(list(section).index(existing[-1]) + 1, reference)
            else:
                section.insert(0, reference)
    reference.set(R + "id", relationship_id)


def fix_cover_xml(document_xml: bytes, relationships_xml: bytes | None = None) -> tuple[bytes, dict[str, Any]]:
    root = etree.fromstring(document_xml)
    body = root.find("w:body", NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)
    ranges = cover_ranges(paragraphs)
    for start, end in ranges:
        for paragraph in paragraphs[start : end + 1]:
            center_paragraph(paragraph)
    sections = body.xpath(".//w:sectPr", namespaces=NS)
    if len(sections) != 3:
        raise ValueError(f"Expected 3 document sections, found {len(sections)}")
    cover_section_end = paragraphs[ranges[0][1]].find("./w:pPr/w:sectPr", NS)
    continuation_section = sections[1]
    inner_cover_section = split_inner_cover_section(paragraphs[ranges[1][1]], continuation_section)
    if cover_section_end is None:
        raise ValueError("The first cover must end at a section boundary")
    set_page_border(sections[0], "firstPage")
    set_vertical_alignment(sections[0], "center")
    title_page = inner_cover_section.find(W + "titlePg")
    if title_page is None:
        title_page = etree.Element(W + "titlePg")
        doc_grid = inner_cover_section.find(W + "docGrid")
        insert_at = list(inner_cover_section).index(doc_grid) if doc_grid is not None else len(inner_cover_section)
        inner_cover_section.insert(insert_at, title_page)
    title_page.set(W + "val", "1")
    if relationships_xml is not None:
        first_header = next((item for item in sections[0].findall(W + "headerReference")
                             if item.get(W + "type") == "first"), None)
        default_footer = next((item for item in inner_cover_section.findall(W + "footerReference")
                               if item.get(W + "type") == "default"), None)
        if first_header is None or default_footer is None:
            raise ValueError("Could not preserve the title-page header/footer references")
        add_first_page_reference(inner_cover_section, "header", first_header.get(R + "id"))
        add_first_page_reference(inner_cover_section, "footer", default_footer.get(R + "id"))
    return xml_bytes(root), {
        "cover_paragraph_ranges": [list(item) for item in ranges],
        "centered_paragraph_count": sum(end - start + 1 for start, end in ranges),
        "section_count": 4,
        "bordered_section_indices": [0, 1],
        "border_display": ["firstPage", "allPages"],
        "border_inset_points": 36,
        "inner_cover_vertical_alignment": "center",
        "inner_cover_isolated_section": True,
        "inner_cover_title_page_header_footer_enabled": True,
    }


def parse_java_enum(source: str, name: str) -> set[str]:
    match = re.search(r"\benum\s+" + re.escape(name) + r"\s*\{([^}]*)\}", source, re.S)
    if not match:
        raise ValueError(f"Enum {name} not found in Java source")
    body = re.sub(r"/\*.*?\*/|//[^\n]*", "", match.group(1), flags=re.S)
    return set(re.findall(r"\b([A-Z][A-Z0-9_]*)\b(?=\s*(?:,|;|$))", body, re.M))


def parse_puml_enum(source: str, name: str) -> set[str]:
    match = re.search(r"\benum\s+" + re.escape(name) + r"\s*\{([^}]*)\}", source, re.S)
    if match:
        return set(re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*$", match.group(1), re.M))
    legend = re.search(r"^\s*" + re.escape(name) + r"\s*:\s*([^\r\n]+)$", source, re.M)
    if legend:
        return {value.strip() for value in legend.group(1).split(",") if value.strip()}
    raise ValueError(f"Enum {name} not found in PlantUML domain diagram or enum legend")


def audit_project(project_root: Path, diagram_root: Path = DIAGRAM_ROOT) -> dict[str, Any]:
    java_root = project_root / "src" / "main" / "java" / "com" / "strongwine" / "strongwine"
    domain = (diagram_root / "erd_oop.puml").read_text(encoding="utf-8-sig")
    enum_results = {}
    errors: list[str] = []
    for name in ENUMS:
        java_path = java_root / "entity" / f"{name}.java"
        if not java_path.is_file():
            errors.append(f"Missing Java enum source: {java_path}")
            continue
        expected = parse_java_enum(java_path.read_text(encoding="utf-8-sig"), name)
        actual = parse_puml_enum(domain, name)
        enum_results[name] = {"java": sorted(expected), "diagram": sorted(actual), "match": expected == actual}
        if expected != actual:
            errors.append(f"Enum mismatch for {name}: Java={sorted(expected)}, diagram={sorted(actual)}")

    diagram_results = {}
    for name, required in REQUIRED_DIAGRAM_TEXT.items():
        path = diagram_root / f"{name}.puml"
        if not path.is_file():
            errors.append(f"Missing diagram source: {path}")
            continue
        source = path.read_text(encoding="utf-8-sig")
        missing = [token for token in required if token not in source]
        forbidden = [token for token in FORBIDDEN_DIAGRAM_TEXT.get(name, ()) if token in source]
        diagram_results[name] = {"missing_required_text": missing, "stale_or_forbidden_text": forbidden}
        if missing:
            errors.append(f"{name} missing required evidence strings: {missing}")
        if forbidden:
            errors.append(f"{name} still contains stale claims: {forbidden}")

    project_checks = {
        "AdminController.java": ("@RequestMapping(\"/admin\")", "return \"admin-dashboard\";"),
        "CartController.java": ("@RequestMapping(\"/cart\")", "/checkout/process"),
        "PaymentController.java": ("@RequestMapping(\"/payment\")", "/webhook", "Stripe-Signature"),
        "WineController.java": ("@RequestMapping(\"/wines\")", "return \"wine-list\";", "/admin/create"),
        "ShipperController.java": ("@RequestMapping(\"/shipper\")", "/shipments/{id}/complete", "/resend-otp"),
    }
    route_results = {}
    for filename, tokens in project_checks.items():
        path = java_root / "controller" / filename
        if not path.is_file():
            errors.append(f"Missing controller source: {path}")
            continue
        source = path.read_text(encoding="utf-8-sig")
        missing = [token for token in tokens if token not in source]
        route_results[filename] = {"checked_tokens": list(tokens), "missing": missing}
        if missing:
            errors.append(f"Controller route evidence missing in {filename}: {missing}")

    screen_route_checks = {}
    reviewed_routes = sorted({
        route
        for facts in PROJECT_MEDIA_FACTS.values()
        for route in facts.get("route_paths", [])
    })
    for route in reviewed_routes:
        assertion = PROJECT_ROUTE_ASSERTIONS.get(route)
        if assertion is None:
            screen_route_checks[route] = {"status": "UNMAPPED"}
            errors.append(f"No source assertion configured for reviewed screen route {route}")
            continue
        filename, tokens = assertion
        path = java_root / "controller" / filename
        if not path.is_file():
            screen_route_checks[route] = {"controller": filename, "status": "MISSING_SOURCE"}
            errors.append(f"Missing controller source for reviewed screen route {route}: {path}")
            continue
        source = path.read_text(encoding="utf-8-sig")
        missing = [token for token in tokens if token not in source]
        screen_route_checks[route] = {
            "controller": filename,
            "checked_tokens": list(tokens),
            "missing": missing,
            "status": "PASS" if not missing else "FAIL",
        }
        if missing:
            errors.append(f"Reviewed screen route {route} no longer matches {filename}: {missing}")

    asset_results = {}
    for caption, relative_path in PROJECT_MEDIA_CAPTIONS.items():
        asset_path = resolve_project_asset(project_root, relative_path)
        if not asset_path.is_file():
            asset_results[caption] = {"source": str(asset_path), "exists": False}
            errors.append(f"Missing reviewed project image asset: {asset_path}")
            continue
        asset_results[caption] = {
            "source": str(asset_path.resolve()),
            "exists": True,
            "sha256": sha256(asset_path.read_bytes()),
            "expected_sha256": PROJECT_MEDIA_EXPECTED_SHA256[caption],
            "hash_matches_reviewed_asset": sha256(asset_path.read_bytes()) == PROJECT_MEDIA_EXPECTED_SHA256[caption],
            "facts_checked_against_controller": PROJECT_MEDIA_FACTS[caption],
        }
        if asset_results[caption]["hash_matches_reviewed_asset"] is False:
            errors.append(
                f"Reviewed project image changed; inspect it and explicitly refresh the expected hash: {asset_path}"
            )

    superseded_assets = {}
    for relative_path, metadata in SUPERSEDED_SCREEN_ASSETS.items():
        asset_path = project_root / Path(relative_path)
        asset_hash = sha256(asset_path.read_bytes()) if asset_path.is_file() else None
        hash_matches = asset_hash == metadata["expected_sha256"] if asset_hash is not None else None
        superseded_assets[relative_path] = {
            "source": str(asset_path.resolve()),
            "exists": asset_path.is_file(),
            "sha256": asset_hash,
            "expected_sha256": metadata["expected_sha256"],
            "hash_matches_reviewed_legacy": hash_matches,
            "do_not_reuse": True,
            "reason": metadata["reason"],
        }
        if asset_hash is not None and not hash_matches:
            errors.append(f"Known superseded screen asset changed; re-audit before reuse: {asset_path}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "project_root": str(project_root.resolve()),
        "project_head": git_head(project_root),
        "enum_checks": enum_results,
        "diagram_checks": diagram_results,
        "route_checks": route_results,
        "screen_route_checks": screen_route_checks,
        "project_image_assets": asset_results,
        "superseded_screen_assets": superseded_assets,
        "errors": errors,
    }


def git_head(project_root: Path) -> str | None:
    head = project_root / ".git" / "HEAD"
    if not head.is_file():
        return None
    value = head.read_text(encoding="utf-8", errors="replace").strip()
    if value.startswith("ref: "):
        ref_path = project_root / ".git" / value[5:]
        if ref_path.is_file():
            return ref_path.read_text(encoding="ascii", errors="replace").strip()
    return value


def render_diagrams(diagram_root: Path, output_root: Path | None = None) -> dict[str, dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "src"))
    from wordassistant.diagrams.plantuml import PlantUMLRenderer

    renderer = PlantUMLRenderer()
    target_root = output_root or diagram_root
    target_root.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in DIAGRAM_CAPTIONS:
        output = target_root / f"{name}.png"
        if name in SCREEN_HIERARCHY_NAMES:
            if not output.is_file():
                raise FileNotFoundError(
                    f"Screen hierarchy PNG is generated from the checked screen inventory first: {output}"
                )
            results[name] = {"output_path": str(output.resolve()), "status": "generated-from-screen-inventory"}
            continue
        source = diagram_root / f"{name}.puml"
        results[name] = renderer.render(source, output_path=output, format="png", timeout_seconds=120)
    return results


def relationships_map(rels_xml: bytes) -> dict[str, str]:
    root = etree.fromstring(rels_xml)
    result = {}
    for rel in root.xpath("./rel:Relationship", namespaces=NS):
        result[rel.get("Id")] = rel.get("Target")
    return result


def package_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("word", target))


def normalized_paragraph_text(paragraph: etree._Element) -> str:
    return " ".join("".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).split())


def literal_paragraph_text(paragraph: etree._Element) -> str:
    """Return authored text while ignoring cached values from Word fields."""
    result = []
    field_results: list[bool] = []
    for node in paragraph.iter():
        if node.tag == W + "fldSimple":
            continue
        if node.tag == W + "fldChar":
            field_type = node.get(W + "fldCharType")
            if field_type == "begin":
                field_results.append(False)
            elif field_type == "separate" and field_results:
                field_results[-1] = True
            elif field_type == "end" and field_results:
                field_results.pop()
            continue
        if node.tag == W + "instrText":
            continue
        if node.tag == W + "t" and not node.xpath("ancestor::w:fldSimple", namespaces=NS):
            if not field_results:
                result.append(node.text or "")
    return " ".join("".join(result).split())


def authored_paragraph_text(paragraph: etree._Element) -> str:
    """Return authored text and the visible result of figure-number SEQ fields."""
    result = []
    field_states: list[dict[str, bool]] = []
    for node in paragraph.iter():
        if node.tag == W + "fldSimple":
            continue
        if node.tag == W + "fldChar":
            field_type = node.get(W + "fldCharType")
            if field_type == "begin":
                field_states.append({"cached": False, "include_sequence": False})
            elif field_type == "separate" and field_states:
                field_states[-1]["cached"] = True
            elif field_type == "end" and field_states:
                field_states.pop()
            continue
        if node.tag == W + "instrText":
            if field_states and "SEQ Hinh" in (node.text or ""):
                field_states[-1]["include_sequence"] = True
            continue
        if node.tag == W + "t" and not node.xpath("ancestor::w:fldSimple", namespaces=NS):
            if not field_states or (field_states[-1]["cached"] and field_states[-1]["include_sequence"]):
                result.append(node.text or "")
    return " ".join("".join(result).split())


def sequence_caption_fields(paragraph: etree._Element) -> list[dict[str, Any]]:
    nodes = list(paragraph.iter())
    stack: list[dict[str, Any]] = []
    spans = []
    for index, node in enumerate(nodes):
        if node.tag == W + "fldChar":
            field_type = node.get(W + "fldCharType")
            if field_type == "begin":
                stack.append({"start": index, "instruction": "", "separate": None})
            elif field_type == "separate" and stack:
                stack[-1]["separate"] = index
            elif field_type == "end" and stack:
                field = stack.pop()
                if "SEQ Hinh" in field["instruction"]:
                    field["end"] = index
                    spans.append(field)
        elif node.tag == W + "instrText" and stack:
            stack[-1]["instruction"] += node.text or ""

    field_ranges = [(field["start"], field["end"]) for field in spans]
    results = []
    for field in spans:
        before = []
        after = []
        cached = []
        for index, node in enumerate(nodes):
            if node.tag != W + "t" or node.xpath("ancestor::w:fldSimple", namespaces=NS):
                continue
            in_any_field = any(start <= index <= end for start, end in field_ranges)
            if index < field["start"] and not in_any_field:
                before.append(node.text or "")
            elif index > field["end"] and not in_any_field:
                after.append(node.text or "")
            elif field["separate"] is not None and field["separate"] < index < field["end"]:
                cached.append(node.text or "")
        prefix = "".join(before).strip()
        suffix = "".join(after).strip()
        result = "".join(cached).strip()
        valid = bool(re.fullmatch(r"Hình\s+\d+\.", prefix)) and suffix.startswith(": ") and bool(re.fullmatch(r"\d+", result))
        results.append({
            "instruction": field["instruction"].strip(),
            "prefix": prefix,
            "suffix": suffix,
            "result": result,
            "valid_position": valid,
        })
    return results


def audit_sequence_caption_fields(paragraphs: list[etree._Element]) -> dict[str, Any]:
    checks = []
    for index, paragraph in enumerate(paragraphs):
        for field in sequence_caption_fields(paragraph):
            checks.append({"paragraph_index": index, **field})
    errors = [item for item in checks if not item["valid_position"]]
    return {"status": "PASS" if not errors else "FAIL", "field_count": len(checks), "checks": checks, "errors": errors}


def repair_misplaced_shipper_caption_sequence(document_root: etree._Element) -> dict[str, Any]:
    """Move the reviewed Hình 5.10 SEQ field into its number and keep the caption title clean."""
    body = document_root.find("w:body", NS)
    if body is None:
        raise ValueError("DOCX has no document body")
    candidates = {
        "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper (ảnh giao diện từ bộ tài liệu dự án)",
        "Hình 5.10: Chỉnh sửa hồ sơ người giao hàng",
    }
    desired = "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper"
    paragraphs = body.xpath("./w:p", namespaces=NS)
    broken = [paragraph for paragraph in paragraphs if literal_paragraph_text(paragraph) in candidates]
    if not broken:
        already_correct = [
            paragraph for paragraph in paragraphs
            if authored_paragraph_text(paragraph) == desired
            and sequence_caption_fields(paragraph)
            and all(field["valid_position"] for field in sequence_caption_fields(paragraph))
        ]
        if len(already_correct) == 1:
            return {"status": "already_correct", "caption": desired}
        return {"status": "not_present", "caption": desired}
    if len(broken) != 1:
        raise ValueError(f"Expected one known misplaced Hình 5.10 caption, found {len(broken)}")

    paragraph = broken[0]
    fields = sequence_caption_fields(paragraph)
    if not fields:
        return {"status": "no_sequence_field", "caption": desired}
    if len(fields) != 1:
        raise ValueError(f"Expected one SEQ Hinh field in the known caption, found {len(fields)}")
    children = list(paragraph)
    start_indices = [i for i, child in enumerate(children)
                     if child.find("w:fldChar", NS) is not None
                     and child.find("w:fldChar", NS).get(W + "fldCharType") == "begin"]
    end_indices = [i for i, child in enumerate(children)
                   if child.find("w:fldChar", NS) is not None
                   and child.find("w:fldChar", NS).get(W + "fldCharType") == "end"]
    if len(start_indices) != 1 or len(end_indices) != 1 or start_indices[0] >= end_indices[0]:
        raise ValueError("Known Hình 5.10 caption has an unexpected field-run structure")
    field_nodes = children[start_indices[0]:end_indices[0] + 1]
    field_runs = [node for node in field_nodes if node.tag == W + "r"]
    bookmark_ends = [node for node in field_nodes if node.tag == W + "bookmarkEnd"]
    if len(field_runs) != len(field_nodes) - len(bookmark_ends) or len(bookmark_ends) > 1:
        raise ValueError("Known Hình 5.10 field contains unsupported OOXML elements")
    caption_runs = [
        child for child in children
        if child.tag == W + "r" and child not in field_runs and child.xpath("./w:t", namespaces=NS)
    ]
    if len(caption_runs) != 1:
        raise ValueError(f"Expected one literal caption run, found {len(caption_runs)}")

    caption_run = caption_runs[0]
    text_nodes = caption_run.xpath("./w:t", namespaces=NS)
    caption_run_copy = deepcopy(caption_run)
    copied_text_nodes = caption_run_copy.xpath("./w:t", namespaces=NS)
    if not text_nodes or not copied_text_nodes:
        raise ValueError("Known Hình 5.10 caption has no editable text run")
    prefix = "Hình 5."
    suffix = ": Giao diện chỉnh sửa hồ sơ Shipper"
    text_nodes[0].text = prefix
    for node in text_nodes[1:]:
        node.text = ""
    copied_text_nodes[0].text = suffix
    for node in copied_text_nodes[1:]:
        node.text = ""

    for node in field_nodes:
        paragraph.remove(node)
    insertion = list(paragraph).index(caption_run) + 1
    for offset, node in enumerate(field_runs):
        paragraph.insert(insertion + offset, node)
    suffix_index = insertion + len(field_runs)
    paragraph.insert(suffix_index, caption_run_copy)
    for offset, node in enumerate(bookmark_ends):
        paragraph.insert(suffix_index + 1 + offset, node)

    if authored_paragraph_text(paragraph) != desired:
        raise ValueError("Hình 5.10 caption repair did not produce the expected visible caption")
    return {"status": "repaired", "caption": desired, "sequence_field": fields[0]["instruction"]}


def preceding_image_for_caption(
    body: etree._Element,
    caption_paragraph: etree._Element,
    rels: dict[str, str],
) -> tuple[etree._Element, str] | None:
    siblings = list(body)
    caption_index = siblings.index(caption_paragraph)
    for candidate in reversed(siblings[:caption_index]):
        blips = candidate.xpath(".//a:blip", namespaces=NS)
        if blips:
            if len(blips) != 1:
                raise ValueError("Caption has an ambiguous preceding image count")
            relationship_id = blips[0].get(R + "embed")
            target = rels.get(relationship_id)
            part = package_target(target) if target else ""
            if not part.startswith("word/media/"):
                raise ValueError(f"Caption resolves to an invalid media target: {target!r}")
            return candidate, part
        if candidate.tag != W + "p" or authored_paragraph_text(candidate):
            break
    return None


def media_part_for_caption(
    document_root: etree._Element,
    rels: dict[str, str],
    caption: str,
) -> str:
    """Resolve the image immediately associated with a body caption via OOXML relationships."""
    return media_part_for_caption_options(document_root, rels, (caption,))


def media_part_for_caption_options(
    document_root: etree._Element,
    rels: dict[str, str],
    captions: tuple[str, ...],
) -> str:
    """Resolve one image for a caption that may have a reviewed legacy wording."""
    body = document_root.find("w:body", NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)
    matches = [paragraph for paragraph in paragraphs if authored_paragraph_text(paragraph) in captions]
    related = [
        preceding_image_for_caption(body, paragraph, rels)
        for paragraph in matches
    ]
    resolved = [item for item in related if item is not None]
    if len(resolved) != 1:
        raise ValueError(
            f"Expected one caption-linked image for one of {captions!r}, found {len(resolved)} "
            f"among {len(matches)} matching caption paragraphs"
        )
    return resolved[0][1]


def resolve_authored_media(document_root: etree._Element, rels: dict[str, str]) -> dict[str, dict[str, str]]:
    diagrams = {
        name: media_part_for_caption(document_root, rels, caption)
        for name, caption in DIAGRAM_CAPTIONS.items()
    }
    project_images = {
        caption: media_part_for_caption_options(
            document_root, rels, (caption, *PROJECT_MEDIA_CAPTION_ALIASES.get(caption, ()))
        )
        for caption in PROJECT_MEDIA_CAPTIONS
    }
    all_parts = list(diagrams.values()) + list(project_images.values())
    if len(all_parts) != len(set(all_parts)):
        raise ValueError("Two authored figures resolve to the same media part; refusing ambiguous media replacement")
    return {"diagrams": diagrams, "project_images": project_images}


def fit_picture_extents(
    document_root: etree._Element,
    rels: dict[str, str],
    media: dict[str, bytes],
    authored_media_parts: set[str],
) -> int:
    max_width = int(5.8 * 914400)
    max_height = int(6.2 * 914400)
    changed = 0
    for drawing in document_root.xpath(".//wp:inline | .//wp:anchor", namespaces=NS):
        blip = drawing.find(".//a:blip", NS)
        extent = drawing.find("wp:extent", NS)
        if blip is None or extent is None:
            continue
        target = rels.get(blip.get(R + "embed"))
        part = package_target(target) if target else ""
        if part not in media or part not in authored_media_parts:
            continue
        with Image.open(__import__("io").BytesIO(media[part])) as image:
            pixel_width, pixel_height = image.size
        current_width, current_height = int(extent.get("cx")), int(extent.get("cy"))
        scale = min(1.0, max_width / current_width, max_height / current_height)
        # Use the replacement raster's aspect ratio while keeping the current displayed width when it fits.
        fitted_width = int(min(max_width, current_width * scale))
        fitted_height = int(fitted_width * pixel_height / pixel_width)
        if fitted_height > max_height:
            fitted_height = max_height
            fitted_width = int(fitted_height * pixel_width / pixel_height)
        extent.set("cx", str(fitted_width))
        extent.set("cy", str(fitted_height))
        transform_extent = drawing.find(".//a:xfrm/a:ext", NS)
        if transform_extent is not None:
            transform_extent.set("cx", str(fitted_width))
            transform_extent.set("cy", str(fitted_height))
        changed += 1
    return changed


def apply_verified_text_edits(
    document_root: etree._Element, replacements: dict[str, str] | None = None
) -> list[dict[str, str]]:
    body = document_root.find("w:body", NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)
    applied = []
    for old_text, new_text in (replacements or VERIFIED_TEXT_EDITS).items():
        acceptable_old_texts = (old_text, *VERIFIED_TEXT_EDIT_ALIASES.get(old_text, ()))
        old_matches = [
            p for p in paragraphs
            if "".join(p.xpath(".//w:t/text()", namespaces=NS)) in acceptable_old_texts
        ]
        if not old_matches:
            if any("".join(p.xpath(".//w:t/text()", namespaces=NS)) == new_text for p in paragraphs):
                continue
            raise ValueError(f"Verified text anchor is missing or changed: {old_text[:90]!r}")
        if len(old_matches) != 1:
            raise ValueError(f"Verified text anchor is ambiguous ({len(old_matches)} matches): {old_text[:90]!r}")
        actual_old_text = "".join(old_matches[0].xpath(".//w:t/text()", namespaces=NS))
        text_nodes = old_matches[0].xpath(".//w:t", namespaces=NS)
        if not text_nodes:
            raise ValueError(f"Text anchor has no editable text run: {old_text[:90]!r}")
        text_nodes[0].text = new_text
        for text_node in text_nodes[1:]:
            text_node.text = ""
        applied.append({"before": actual_old_text, "after": new_text})
    return applied


def apply_caption_text_edits(
    document_root: etree._Element, replacements: dict[str, str]
) -> list[dict[str, str]]:
    """Rename exact caption text while preserving TOF hyperlinks and page fields."""
    body = document_root.find("w:body", NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)
    applied = []
    for old_text, new_text in replacements.items():
        matches = [p for p in paragraphs if authored_paragraph_text(p) == old_text]
        if not matches:
            if any(authored_paragraph_text(p) == new_text for p in paragraphs):
                continue
            raise ValueError(f"Verified caption anchor is missing or changed: {old_text[:90]!r}")
        changed_nodes = 0
        for paragraph in matches:
            nodes = [node for node in paragraph.xpath(".//w:t", namespaces=NS) if node.text == old_text]
            if len(nodes) != 1:
                raise ValueError(
                    f"Expected one exact caption text node in each matching paragraph, found {len(nodes)}"
                )
            nodes[0].text = new_text
            changed_nodes += 1
        applied.append({"before": old_text, "after": new_text, "paragraphs_updated": changed_nodes})
    return applied


def remove_known_misleading_figures(
    document_root: etree._Element,
    rels: dict[str, str],
    media: dict[str, bytes],
    project_root: Path,
) -> list[dict[str, str]]:
    """Remove only reviewed caption/image pairs whose source bytes prove the known mismatch."""
    body = document_root.find("w:body", NS)
    if body is None:
        raise ValueError("DOCX has no document body")
    removed = []
    for caption, rule in MISLEADING_FIGURE_RULES.items():
        caption_matches = [
            node for node in body.xpath("./w:p", namespaces=NS)
            if authored_paragraph_text(node) == caption
        ]
        related = [
            (node, preceding_image_for_caption(body, node, rels))
            for node in caption_matches
        ]
        attached = [(node, image) for node, image in related if image is not None]
        if not attached:
            continue  # Already removed, or only a stale table-of-figures field remains.
        if len(attached) != 1:
            raise ValueError(f"Expected one image-linked known misleading caption {caption!r}, found {len(attached)}")
        caption_node, (image_node, part) = attached[0]

        source_path = project_root / Path(rule["source"])
        if not source_path.is_file():
            raise ValueError(f"Reviewed source for misleading figure is missing: {source_path}")
        source_bytes = source_path.read_bytes()
        if sha256(source_bytes) != rule["expected_sha256"]:
            raise ValueError(f"Reviewed source changed for misleading figure; re-audit before removal: {source_path}")
        if media.get(part) != source_bytes:
            raise ValueError(f"Figure media does not match the reviewed source asset for {caption!r}")

        body.remove(image_node)
        body.remove(caption_node)
        removed.append({
            "caption": caption,
            "media_part": part,
            "source": str(source_path.resolve()),
            "sha256": sha256(source_bytes),
            "reason": rule["reason"],
        })
    return removed


def home_wireframe_image_paragraph(
    document_root: etree._Element, rels: dict[str, str]
) -> tuple[etree._Element, str]:
    body = document_root.find("w:body", NS)
    if body is None:
        raise ValueError("DOCX has no document body")
    caption = "Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine (Grayscale Web Mockup)"
    matches = [p for p in body.xpath("./w:p", namespaces=NS) if authored_paragraph_text(p) == caption]
    linked = [preceding_image_for_caption(body, p, rels) for p in matches]
    linked = [item for item in linked if item is not None]
    if len(linked) != 1:
        raise ValueError(f"Expected one home wireframe caption/image pair, found {len(linked)}")
    return linked[0]


def remove_stray_number_before_home_wireframe(
    document_root: etree._Element, rels: dict[str, str]
) -> dict[str, Any]:
    """Remove the empty numbered-list marker that rendered as a stray 3.51."""
    image_paragraph, _part = home_wireframe_image_paragraph(document_root, rels)
    caption = "Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine (Grayscale Web Mockup)"
    if authored_paragraph_text(image_paragraph):
        raise ValueError("Refusing to change numbering on a non-empty paragraph before the home wireframe")
    ppr = image_paragraph.find(W + "pPr")
    num_pr = ppr.find(W + "numPr") if ppr is not None else None
    if num_pr is None:
        return {"status": "already_correct", "caption": caption}
    ppr.remove(num_pr)
    return {"status": "removed", "caption": caption, "removed_property": "w:numPr"}


def reorder_admin_illustrations(document_root: etree._Element) -> dict[str, Any]:
    """Place Chapter 5 figures with the admin content they illustrate."""
    body = document_root.find("w:body", NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)

    def paragraph_text(paragraph: etree._Element) -> str:
        return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()

    def unique_paragraph(anchor: str) -> etree._Element:
        matches = [paragraph for paragraph in paragraphs if paragraph_text(paragraph) == anchor]
        if len(matches) != 1:
            raise ValueError(f"Expected one figure-order anchor {anchor!r}, found {len(matches)}")
        return matches[0]

    chapter5 = unique_paragraph("CHƯƠNG 5: LUỒNG NGHIỆP VỤ QUẢN TRỊ VÀ KHO")
    dashboard_section = unique_paragraph("Dashboard và quản lý danh mục, sản phẩm")
    sequence_caption = unique_paragraph(
        "Hình 5.2: Sơ đồ tuần tự (Sequence Diagram) Admin thêm rượu và lưu ảnh qua FileStorageService"
    )
    h53 = unique_paragraph("Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI (Grayscale Web Mockup)")
    h50 = unique_paragraph(
        "Hình 5.0: Sơ đồ phân rã màn hình phân hệ Quản trị và Thủ kho (Admin & Warehouse Screen Hierarchy Tree)"
    )
    h50b = unique_paragraph("Hình 5.0b: Sơ đồ Use Case chi tiết phân hệ Quản trị và Thủ kho")
    h54 = unique_paragraph("Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang (Grayscale Web Mockup)")
    h55 = unique_paragraph("Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu (Grayscale Web Mockup)")

    def range_for(first: etree._Element, last: etree._Element) -> list[etree._Element]:
        nodes = list(body)
        start, end = nodes.index(first), nodes.index(last)
        if start > end:
            raise ValueError("Figure-order range is reversed")
        return nodes[start : end + 1]

    dashboard_nodes = range_for(paragraphs[paragraphs.index(h53) - 2], h53)
    overview_nodes = range_for(paragraphs[paragraphs.index(h50) - 2], paragraphs[paragraphs.index(h50b) + 1])
    product_nodes = range_for(body.xpath("./w:p", namespaces=NS)[body.xpath("./w:p", namespaces=NS).index(h54) - 1], h55)
    groups = [dashboard_nodes, overview_nodes, product_nodes]
    flattened = [node for group in groups for node in group]
    if len(flattened) != len(set(flattened)):
        raise ValueError("Admin figure groups overlap")
    targets = [chapter5, dashboard_section, sequence_caption]
    if any(target in flattened for target in targets):
        raise ValueError("A Chapter 5 insertion anchor overlaps a moved figure group")

    for group in groups:
        for node in group:
            body.remove(node)

    def insert_after(target: etree._Element, nodes: list[etree._Element]) -> None:
        anchor = target
        for node in nodes:
            anchor.addnext(node)
            anchor = node

    insert_after(chapter5, overview_nodes)
    insert_after(dashboard_section, dashboard_nodes)
    insert_after(sequence_caption, product_nodes)
    return {
        "moved_groups": ["chapter5_overview", "dashboard_wireframe", "wine_list_and_form_wireframes"],
        "order": ["Hình 5.0", "Hình 5.0b", "Hình 5.3", "Hình 5.1", "Hình 5.2", "Hình 5.4", "Hình 5.5"],
    }


def audit_admin_figure_order(paragraphs: list[etree._Element]) -> dict[str, Any]:
    def text(paragraph: etree._Element) -> str:
        return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()

    anchors = {
        "chapter5": "CHƯƠNG 5: LUỒNG NGHIỆP VỤ QUẢN TRỊ VÀ KHO",
        "h50": "Hình 5.0: Sơ đồ phân rã màn hình phân hệ Quản trị và Thủ kho (Admin & Warehouse Screen Hierarchy Tree)",
        "h50b": "Hình 5.0b: Sơ đồ Use Case chi tiết phân hệ Quản trị và Thủ kho",
        "dashboard_section": "Dashboard và quản lý danh mục, sản phẩm",
        "h53": "Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI (Grayscale Web Mockup)",
        "h51": "Hình 5.1: Sơ đồ hoạt động (Activity Diagram) Quản trị viên thêm rượu và upload ảnh",
        "h52": "Hình 5.2: Sơ đồ tuần tự Admin tạo rượu qua form MVC và FileStorageService",
        "h54": "Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang (Grayscale Web Mockup)",
        "h55": "Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu (Grayscale Web Mockup)",
    }
    matches = {key: [i for i, paragraph in enumerate(paragraphs) if text(paragraph) == value] for key, value in anchors.items()}
    unique = all(len(indices) == 1 for indices in matches.values())
    indices = {key: values[0] for key, values in matches.items() if len(values) == 1}
    expected = ["chapter5", "h50", "h50b", "dashboard_section", "h53", "h51", "h52", "h54", "h55"]
    ordered = unique and [indices[key] for key in expected] == sorted(indices[key] for key in expected)
    return {"unique_anchors": unique, "expected_order": expected, "positions": indices, "ordered": ordered}


def update_visuals_copy(
    input_path: Path,
    output_path: Path,
    rendered: dict[str, dict[str, Any]],
    project_root: Path,
) -> dict[str, Any]:
    """Refresh verified figures in a copy of an already corrected DOCX.

    This path preserves the supplied v2 document structure and updates reviewed
    figure assets, verified prose and captions, and the known empty list marker.
    It deliberately does not re-run cover or section surgery.
    """
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
    with zipfile.ZipFile(input_path, "r") as source_zip:
        entries = {info.filename: (info, source_zip.read(info.filename)) for info in source_zip.infolist()}
    for required in ("word/document.xml", "word/_rels/document.xml.rels"):
        if required not in entries:
            raise ValueError(f"Input is missing required DOCX part {required}")

    document_root = etree.fromstring(entries["word/document.xml"][1])
    rels = relationships_map(entries["word/_rels/document.xml.rels"][1])
    stray_number = remove_stray_number_before_home_wireframe(document_root, rels)
    content_edits = apply_verified_text_edits(document_root)
    caption_edits = apply_caption_text_edits(document_root, {
        "Hình 6.2: Wireframe đề xuất chi tiết vận đơn và Google Maps Shipper (Grayscale Web Mockup)":
        "Hình 6.2: Wireframe trạng thái xem chi tiết vận đơn trên bảng điều khiển Shipper",
        "Hình 6.3: Wireframe đề xuất màn hình OTP riêng cho Shipper (Grayscale Web Mockup)":
        "Hình 6.3: Wireframe trạng thái nhập OTP hoàn tất giao hàng trên bảng điều khiển Shipper",
    })
    authored = resolve_authored_media(document_root, rels)
    media_bytes: dict[str, bytes] = {}
    replaced = []

    for diagram_name, part in authored["diagrams"].items():
        if part not in entries:
            raise ValueError(f"Missing embedded media for diagram {DIAGRAM_CAPTIONS[diagram_name]!r}: {part}")
        image_bytes = Path(rendered[diagram_name]["output_path"]).read_bytes()
        entries[part] = (entries[part][0], image_bytes)
        media_bytes[part] = image_bytes
        replaced.append({"part": part, "kind": "diagram", "name": diagram_name, "sha256": sha256(image_bytes)})

    for caption, part in authored["project_images"].items():
        source_path = resolve_project_asset(project_root, PROJECT_MEDIA_CAPTIONS[caption])
        if part not in entries or not source_path.is_file():
            raise ValueError(f"Missing reviewed project image: {part} <- {source_path}")
        image_bytes = source_path.read_bytes()
        entries[part] = (entries[part][0], image_bytes)
        media_bytes[part] = image_bytes
        replaced.append({
            "part": part, "kind": "project-image", "caption": caption,
            "source": str(source_path.resolve()), "sha256": sha256(image_bytes),
        })

    resized = fit_picture_extents(document_root, rels, media_bytes, set(media_bytes))
    entries["word/document.xml"] = (entries["word/document.xml"][0], xml_bytes(document_root))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as output_zip:
        for name, (info, content) in entries.items():
            output_zip.writestr(info, content)
    return {
        "input": str(input_path.resolve()), "input_sha256": sha256(input_path.read_bytes()),
        "output": str(output_path.resolve()), "output_sha256": sha256(output_path.read_bytes()),
        "removed_stray_number": stray_number, "content_edits": content_edits,
        "caption_edits": caption_edits,
        "replaced_media": replaced, "resized_picture_instances": resized,
    }


def update_docx(
    input_path: Path,
    output_path: Path,
    rendered: dict[str, dict[str, Any]],
    project_root: Path,
) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
    with zipfile.ZipFile(input_path, "r") as source_zip:
        entries = {info.filename: (info, source_zip.read(info.filename)) for info in source_zip.infolist()}
    if "word/document.xml" not in entries or "word/_rels/document.xml.rels" not in entries:
        raise ValueError("Input is not a valid Word DOCX package")
    document_xml, cover_result = fix_cover_xml(
        entries["word/document.xml"][1], entries["word/_rels/document.xml.rels"][1]
    )
    document_root = etree.fromstring(document_xml)
    rels = relationships_map(entries["word/_rels/document.xml.rels"][1])
    source_media = {
        name: data for name, (_info, data) in entries.items() if name.startswith("word/media/")
    }
    removed_misleading_figures = remove_known_misleading_figures(
        document_root, rels, source_media, project_root
    )
    illustration_order = reorder_admin_illustrations(document_root)
    caption_sequence_repair = repair_misplaced_shipper_caption_sequence(document_root)
    content_edits = apply_verified_text_edits(document_root)
    entries["word/document.xml"] = (entries["word/document.xml"][0], document_xml)
    authored_parts = resolve_authored_media(document_root, rels)
    replaced = []
    media_bytes: dict[str, bytes] = {}
    for diagram_name, part in authored_parts["diagrams"].items():
        if part not in entries:
            raise ValueError(f"Expected embedded DOCX media is missing for {DIAGRAM_CAPTIONS[diagram_name]!r}: {part}")
        diagram_png = Path(rendered[diagram_name]["output_path"]).read_bytes()
        entries[part] = (entries[part][0], diagram_png)
        media_bytes[part] = diagram_png
        replaced.append({
            "media_part": part,
            "caption": DIAGRAM_CAPTIONS[diagram_name],
            "diagram": diagram_name,
            "sha256": sha256(diagram_png),
        })
    for caption, part in authored_parts["project_images"].items():
        relative_path = PROJECT_MEDIA_CAPTIONS[caption]
        asset_path = resolve_project_asset(project_root, relative_path)
        if part not in entries or not asset_path.is_file():
            raise ValueError(f"Reviewed project image asset is missing: {part} <- {asset_path}")
        asset_bytes = asset_path.read_bytes()
        entries[part] = (entries[part][0], asset_bytes)
        media_bytes[part] = asset_bytes
        replaced.append({
            "media_part": part,
            "caption": caption,
            "source_asset": str(asset_path.resolve()),
            "sha256": sha256(asset_bytes),
        })
    extent_count = fit_picture_extents(document_root, rels, media_bytes, set(media_bytes))
    entries["word/document.xml"] = (entries["word/document.xml"][0], xml_bytes(document_root))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as result_zip:
        for name, (info, content) in entries.items():
            result_zip.writestr(info, content)
    return {
        "input": str(input_path.resolve()),
        "input_sha256": sha256(input_path.read_bytes()),
        "output": str(output_path.resolve()),
        "output_sha256": sha256(output_path.read_bytes()),
        "cover": cover_result,
        "illustration_order": illustration_order,
        "caption_sequence_repair": caption_sequence_repair,
        "verified_content_edits": content_edits,
        "removed_misleading_figures": removed_misleading_figures,
        "replaced_diagrams": replaced,
        "resized_picture_instances": extent_count,
    }


def restore_authored_media(
    docx_path: Path,
    project_root: Path,
    diagram_root: Path = DIAGRAM_ROOT,
) -> dict[str, Any]:
    """Restore authored PNG bytes after Word updates fields and may downsample images."""
    with zipfile.ZipFile(docx_path, "r") as archive:
        entries = {info.filename: (info, archive.read(info.filename)) for info in archive.infolist()}
    for required in ("word/document.xml", "word/_rels/document.xml.rels"):
        if required not in entries:
            raise ValueError(f"Input is missing required DOCX part {required}")

    document_root = etree.fromstring(entries["word/document.xml"][1])
    rels = relationships_map(entries["word/_rels/document.xml.rels"][1])
    authored_parts = resolve_authored_media(document_root, rels)
    restored = []
    media_bytes: dict[str, bytes] = {}
    for diagram_name, part in authored_parts["diagrams"].items():
        source_path = diagram_root / f"{diagram_name}.png"
        if part not in entries or not source_path.is_file():
            raise ValueError(f"Cannot restore diagram for {DIAGRAM_CAPTIONS[diagram_name]!r}: {part} from {source_path}")
        data = source_path.read_bytes()
        entries[part] = (entries[part][0], data)
        media_bytes[part] = data
        restored.append({
            "part": part,
            "caption": DIAGRAM_CAPTIONS[diagram_name],
            "source": str(source_path.resolve()),
            "sha256": sha256(data),
        })

    for caption, part in authored_parts["project_images"].items():
        relative_path = PROJECT_MEDIA_CAPTIONS[caption]
        source_path = resolve_project_asset(project_root, relative_path)
        if part not in entries or not source_path.is_file():
            raise ValueError(f"Cannot restore project image media {part} from {source_path}")
        data = source_path.read_bytes()
        entries[part] = (entries[part][0], data)
        media_bytes[part] = data
        restored.append({
            "part": part,
            "caption": caption,
            "source": str(source_path.resolve()),
            "sha256": sha256(data),
        })

    resized = fit_picture_extents(document_root, rels, media_bytes, set(media_bytes))
    entries["word/document.xml"] = (entries["word/document.xml"][0], xml_bytes(document_root))

    temporary_path = docx_path.with_name(docx_path.stem + ".media-restore.tmp.docx")
    if temporary_path.exists():
        raise FileExistsError(f"Refusing to overwrite media-restore temporary file: {temporary_path}")
    with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED) as result_zip:
        for name, (info, data) in entries.items():
            result_zip.writestr(info, data)
    os.replace(temporary_path, docx_path)
    return {
        "docx": str(docx_path.resolve()),
        "docx_sha256": sha256(docx_path.read_bytes()),
        "restored_media": restored,
        "resized_picture_instances": resized,
    }


def repair_caption_sequence_copy(input_path: Path, output_path: Path) -> dict[str, Any]:
    """Create a new DOCX copy with the reviewed misplaced Hình 5.10 SEQ field repaired."""
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Caption repair requires a distinct output DOCX")
    with zipfile.ZipFile(input_path, "r") as source_zip:
        entries = {info.filename: (info, source_zip.read(info.filename)) for info in source_zip.infolist()}
    document_part = "word/document.xml"
    if document_part not in entries:
        raise ValueError("Input DOCX is missing word/document.xml")
    document_root = etree.fromstring(entries[document_part][1])
    repair = repair_misplaced_shipper_caption_sequence(document_root)
    if repair["status"] != "repaired":
        raise ValueError(f"Expected a misplaced Hình 5.10 sequence field to repair, got {repair['status']}")
    entries[document_part] = (entries[document_part][0], xml_bytes(document_root))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as result_zip:
        for name, (info, content) in entries.items():
            result_zip.writestr(info, content)
    return {
        "input": str(input_path.resolve()),
        "input_sha256": sha256(input_path.read_bytes()),
        "output": str(output_path.resolve()),
        "output_sha256": sha256(output_path.read_bytes()),
        "caption_sequence_repair": repair,
    }


def audit_docx(docx_path: Path, project_root: Path, diagram_root: Path = DIAGRAM_ROOT) -> dict[str, Any]:
    with zipfile.ZipFile(docx_path, "r") as archive:
        document_xml = archive.read("word/document.xml")
        rels_xml = archive.read("word/_rels/document.xml.rels")
        styles_xml = archive.read("word/styles.xml")
        media = {name: archive.read(name) for name in archive.namelist() if name.startswith("word/media/")}
    root = etree.fromstring(document_xml)
    rels = relationships_map(rels_xml)
    media_mapping_error = None
    try:
        authored_parts = resolve_authored_media(root, rels)
    except ValueError as exc:
        authored_parts = {"diagrams": {}, "project_images": {}}
        media_mapping_error = str(exc)

    project_media_checks = []
    for caption, relative_path in PROJECT_MEDIA_CAPTIONS.items():
        part = authored_parts["project_images"].get(caption)
        source_path = resolve_project_asset(project_root, relative_path)
        embedded_bytes = media.get(part) if part else None
        source_bytes = source_path.read_bytes() if source_path.is_file() else None
        project_media_checks.append({
            "caption": caption,
            "part": part,
            "source": str(source_path.resolve()),
            "source_exists": source_bytes is not None,
            "embedded_sha256": sha256(embedded_bytes) if embedded_bytes is not None else None,
            "source_sha256": sha256(source_bytes) if source_bytes is not None else None,
            "matches_source": embedded_bytes is not None and source_bytes is not None and embedded_bytes == source_bytes,
            "reviewed_facts": PROJECT_MEDIA_FACTS[caption],
        })

    diagram_checks = []
    for diagram_name, caption in DIAGRAM_CAPTIONS.items():
        part = authored_parts["diagrams"].get(diagram_name)
        embedded_bytes = media.get(part) if part else None
        expected_path = diagram_root / f"{diagram_name}.png"
        expected_bytes = expected_path.read_bytes() if expected_path.is_file() else None
        diagram_checks.append({
            "diagram": diagram_name,
            "caption": caption,
            "part": part,
            "expected_source": str(expected_path.resolve()),
            "expected_exists": expected_bytes is not None,
            "embedded_sha256": sha256(embedded_bytes) if embedded_bytes is not None else None,
            "expected_sha256": sha256(expected_bytes) if expected_bytes is not None else None,
            "matches_source": embedded_bytes is not None and expected_bytes is not None and embedded_bytes == expected_bytes,
        })

    body = root.find("w:body", NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)
    style_alignments = paragraph_style_alignments(styles_xml)
    ranges = cover_ranges(paragraphs)
    alignment = []
    for start, end in ranges:
        values = []
        for paragraph in paragraphs[start : end + 1]:
            values.append(paragraph_is_centered(paragraph, style_alignments))
        alignment.append({"range": [start, end], "all_centered": all(values), "paragraph_count": len(values)})
    sections = body.xpath(".//w:sectPr", namespaces=NS)
    borders = []
    for index, section in enumerate(sections):
        border = section.find("w:pgBorders", NS)
        border_display = border.get(W + "display") if border is not None else None
        if border is not None and border_display is None:
            border_display = "allPages"  # Word omits the OOXML default when saving its native format.
        # Word omits offsetFrom="text" when saving the native DOCX; render QA
        # independently verifies the resulting physical inset on both covers.
        border_offset = border.get(W + "offsetFrom") if border is not None else None
        if border is not None and border_offset is None:
            border_offset = "text"
        page_margins = section.find("w:pgMar", NS)
        borders.append({
            "section_index": index,
            "present": border is not None,
            "display": border_display,
            "offset_from": border_offset,
            "edge_count": len(border) if border is not None else 0,
            "space_points": border[0].get(W + "space") if border is not None and len(border) else None,
            "header_distance_twips": page_margins.get(W + "header") if page_margins is not None else None,
            "footer_distance_twips": page_margins.get(W + "footer") if page_margins is not None else None,
            "title_page_enabled": section.find("w:titlePg", NS) is not None,
            "vertical_alignment": (
                section.find("w:vAlign", NS).get(W + "val")
                if section.find("w:vAlign", NS) is not None else "top"
            ),
            "first_page_header": any(item.get(W + "type") == "first" for item in section.findall(W + "headerReference")),
            "first_page_footer": any(item.get(W + "type") == "first" for item in section.findall(W + "footerReference")),
        })
    crop_count = len(root.xpath(".//a:srcRect", namespaces=NS))
    embedded = []
    ratios = []
    for drawing in root.xpath(".//wp:inline | .//wp:anchor", namespaces=NS):
        blip = drawing.find(".//a:blip", NS)
        extent = drawing.find("wp:extent", NS)
        if blip is None or extent is None:
            continue
        target = rels.get(blip.get(R + "embed"))
        part = package_target(target) if target else ""
        if part not in media:
            continue
        with Image.open(__import__("io").BytesIO(media[part])) as image:
            pixel_width, pixel_height = image.size
        doc_ratio = int(extent.get("cx")) / int(extent.get("cy"))
        pixel_ratio = pixel_width / pixel_height
        diff = abs(doc_ratio - pixel_ratio) / pixel_ratio
        ratios.append(diff)
        embedded.append({"part": part, "width_px": pixel_width, "height_px": pixel_height, "aspect_error": round(diff, 6)})
    paragraph_texts = ["".join(p.xpath(".//w:t/text()", namespaces=NS)) for p in paragraphs]
    authored_texts = [authored_paragraph_text(p) for p in paragraphs]
    caption_sequence_audit = audit_sequence_caption_fields(paragraphs)
    admin_figure_order = audit_admin_figure_order(paragraphs)
    try:
        home_image_paragraph, _home_part = home_wireframe_image_paragraph(root, rels)
        home_ppr = home_image_paragraph.find(W + "pPr")
        stray_home_number = home_ppr is not None and home_ppr.find(W + "numPr") is not None
    except ValueError:
        stray_home_number = None
    misleading_figure_captions_present = [
        caption for caption in MISLEADING_FIGURE_RULES if any(caption in text for text in paragraph_texts)
    ]
    missing_verified_content = [new for new in VERIFIED_TEXT_EDITS.values() if new not in authored_texts]
    prior_verified_text = [
        text
        for old in VERIFIED_TEXT_EDITS
        for text in (old, *VERIFIED_TEXT_EDIT_ALIASES.get(old, ()))
    ]
    stale_source_content = [old[:90] for old in prior_verified_text if old in authored_texts]
    content_status = not missing_verified_content and not stale_source_content
    cover_section_breaks = [
        paragraphs[end].find("./w:pPr/w:sectPr", NS) is not None
        for _start, end in ranges
    ]
    return {
        "path": str(docx_path.resolve()),
        "sha256": sha256(docx_path.read_bytes()),
        "cover_alignment": alignment,
        "cover_section_breaks": cover_section_breaks,
        "page_borders": borders,
        "inline_image_count": len(embedded),
        "unique_media_count": len(media),
        "crop_rect_count": crop_count,
        "max_image_aspect_error": round(max(ratios, default=0.0), 6),
        "verified_content_edit_count": len(VERIFIED_TEXT_EDITS),
        "missing_verified_content": missing_verified_content,
        "stale_source_content": stale_source_content,
        "misleading_figure_captions_present": misleading_figure_captions_present,
        "stray_number_before_home_wireframe": stray_home_number,
        "caption_sequence_fields": caption_sequence_audit,
        "diagrams": diagram_checks,
        "media_mapping_error": media_mapping_error,
        "project_image_assets": project_media_checks,
        "section_count": len(sections),
        "admin_figure_order": admin_figure_order,
        "status": "PASS" if all(item["all_centered"] for item in alignment)
        and len(sections) == 4 and all(cover_section_breaks)
        and all(item["vertical_alignment"] == "center" for item in borders[:2])
        and borders[0]["present"] and borders[0]["display"] == "firstPage"
        and borders[1]["present"] and borders[1]["display"] in {"allPages", "all"}
        and borders[1]["title_page_enabled"] and borders[1]["first_page_header"] and borders[1]["first_page_footer"]
        and all(item["offset_from"] == "text" and item["space_points"] == "4"
                and int(item["header_distance_twips"]) >= 900 and int(item["footer_distance_twips"]) >= 900
                for item in borders[:2])
        and not any(item["present"] for item in borders[2:])
        and media_mapping_error is None
        and all(item["matches_source"] for item in diagram_checks)
        and all(item["matches_source"] for item in project_media_checks)
        and not misleading_figure_captions_present
        and stray_home_number is False
        and caption_sequence_audit["status"] == "PASS"
        and admin_figure_order["ordered"]
        and crop_count == 0 and max(ratios, default=0.0) <= 0.01 and content_status else "FAIL",
    }


def write_report(path: Path | None, report: dict[str, Any]) -> None:
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit", help="Read-only project and DOCX audit")
    audit_parser.add_argument("--input", type=Path, required=True)
    audit_parser.add_argument("--project-root", type=Path, required=True)
    audit_parser.add_argument("--diagram-root", type=Path, default=DIAGRAM_ROOT)
    audit_parser.add_argument("--report", type=Path)
    prepare_parser = subparsers.add_parser("prepare", help="Render verified diagrams and create a corrected DOCX copy")
    prepare_parser.add_argument("--input", type=Path, required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--project-root", type=Path, required=True)
    prepare_parser.add_argument("--diagram-root", type=Path, default=DIAGRAM_ROOT)
    prepare_parser.add_argument("--report", type=Path)
    visuals_parser = subparsers.add_parser(
        "update-visuals", help="Refresh diagrams and verified project figures in a corrected DOCX copy"
    )
    visuals_parser.add_argument("--input", type=Path, required=True)
    visuals_parser.add_argument("--output", type=Path, required=True)
    visuals_parser.add_argument("--project-root", type=Path, required=True)
    visuals_parser.add_argument("--diagram-root", type=Path, default=DIAGRAM_ROOT)
    visuals_parser.add_argument("--report", type=Path)
    restore_parser = subparsers.add_parser("restore-media", help="Restore authored image bytes after Word field updates")
    restore_parser.add_argument("--input", type=Path, required=True)
    restore_parser.add_argument("--project-root", type=Path, required=True)
    restore_parser.add_argument("--diagram-root", type=Path, default=DIAGRAM_ROOT)
    restore_parser.add_argument("--report", type=Path)
    repair_parser = subparsers.add_parser(
        "repair-caption-sequence", help="Create a copy with the reviewed misplaced Hình 5.10 SEQ field repaired"
    )
    repair_parser.add_argument("--input", type=Path, required=True)
    repair_parser.add_argument("--output", type=Path, required=True)
    repair_parser.add_argument("--project-root", type=Path, required=True)
    repair_parser.add_argument("--diagram-root", type=Path, default=DIAGRAM_ROOT)
    repair_parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    project = audit_project(args.project_root, args.diagram_root)
    if project["status"] != "PASS":
        print(json.dumps({"project_audit": project}, ensure_ascii=False, indent=2))
        return 2
    if args.command == "audit":
        docx = audit_docx(args.input, args.project_root, args.diagram_root)
        report = {"created_utc": datetime.now(timezone.utc).isoformat(), "project": project, "docx": docx,
                  "status": "PASS" if docx["status"] == "PASS" else "FAIL"}
    elif args.command == "restore-media":
        restored = restore_authored_media(args.input, args.project_root, args.diagram_root)
        report = {"created_utc": datetime.now(timezone.utc).isoformat(), "project": project,
                  "restore_media": restored, "status": "PASS"}
    elif args.command == "repair-caption-sequence":
        repaired = repair_caption_sequence_copy(args.input, args.output)
        report = {"created_utc": datetime.now(timezone.utc).isoformat(), "project": project,
                  "caption_repair": repaired, "status": "PASS"}
    elif args.command == "update-visuals":
        rendered = render_diagrams(args.diagram_root)
        updated = update_visuals_copy(args.input, args.output, rendered, args.project_root)
        docx = audit_docx(args.output, args.project_root, args.diagram_root)
        report = {"created_utc": datetime.now(timezone.utc).isoformat(), "project": project,
                  "update_visuals": updated, "rendered_diagrams": rendered, "docx": docx,
                  "status": "PASS" if docx["status"] == "PASS" else "FAIL"}
    else:
        rendered = render_diagrams(args.diagram_root)
        prepared = update_docx(args.input, args.output, rendered, args.project_root)
        docx = audit_docx(args.output, args.project_root, args.diagram_root)
        report = {"created_utc": datetime.now(timezone.utc).isoformat(), "project": project,
                  "prepare": prepared, "rendered_diagrams": rendered, "docx": docx,
                  "status": "PASS" if docx["status"] == "PASS" else "FAIL"}
    write_report(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
