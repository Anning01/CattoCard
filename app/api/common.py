"""通用API（文件上传等）"""

from fastapi import APIRouter, File, UploadFile

from app.core.exceptions import BadRequestException
from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.services.upload import delete_upload_file, save_upload_file

router = APIRouter()


@router.post("/upload", response_model=ResponseModel, summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    subdir: str = "",
):
    """
    上传文件（图片、图标等）
    
    - 支持格式: jpg, jpeg, png, gif, webp, svg, ico
    - 最大大小: 10MB
    - 返回文件访问URL
    
    subdir 可选值:
    - images: 商品图片
    - icons: 图标
    - banners: 轮播图
    - 留空: 通用文件
    """
    if not file.filename:
        raise BadRequestException(message="文件名不能为空")
    
    logger.info(f"上传文件: {file.filename}, content_type={file.content_type}, subdir={subdir}")
    
    # 读取文件内容
    content = await file.read()
    
    if not content:
        raise BadRequestException(message="文件内容为空")
    
    # 保存文件
    url = await save_upload_file(content, file.filename, subdir)
    
    return success_response(
        data={"url": url, "filename": file.filename},
        message="上传成功",
    )


@router.post("/upload/batch", response_model=ResponseModel, summary="批量上传文件")
async def upload_files(
    files: list[UploadFile] = File(..., description="要上传的文件列表"),
    subdir: str = "",
):
    """
    批量上传文件
    
    - 支持格式: jpg, jpeg, png, gif, webp, svg, ico
    - 单个文件最大: 10MB
    - 返回所有文件访问URL列表
    """
    if not files:
        raise BadRequestException(message="请选择要上传的文件")
    
    logger.info(f"批量上传文件: {len(files)} 个文件, subdir={subdir}")
    
    results = []
    errors = []
    
    for file in files:
        if not file.filename:
            errors.append({"filename": "unknown", "error": "文件名为空"})
            continue
        
        try:
            content = await file.read()
            if not content:
                errors.append({"filename": file.filename, "error": "文件内容为空"})
                continue
            
            url = await save_upload_file(content, file.filename, subdir)
            results.append({"url": url, "filename": file.filename})
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    return success_response(
        data={"uploaded": results, "errors": errors},
        message=f"成功上传 {len(results)} 个文件" + (f"，{len(errors)} 个失败" if errors else ""),
    )


@router.delete("/upload", response_model=ResponseModel, summary="删除文件")
async def remove_file(url: str):
    """
    删除已上传的文件
    
    - url: 文件访问URL（如 /static/2024/01/15/xxx.jpg）
    """
    if not url:
        raise BadRequestException(message="文件URL不能为空")
    
    logger.info(f"删除文件: {url}")
    
    success = delete_upload_file(url)
    
    if success:
        return success_response(message="删除成功")
    else:
        raise BadRequestException(message="文件不存在或删除失败")
