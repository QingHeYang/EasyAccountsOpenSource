/**
 * 图片压缩工具
 * 用于在上传前压缩图片，减少上传时间和服务器存储空间
 */

/**
 * 压缩图片
 * @param {File} file - 原始图片文件
 * @param {Object} options - 压缩选项
 * @param {number} options.maxWidth - 最大宽度，默认 1920
 * @param {number} options.maxHeight - 最大高度，默认 1920
 * @param {number} options.quality - 压缩质量 0-1，默认 0.8
 * @param {number} options.maxSizeMB - 最大文件大小（MB），默认 2MB
 * @returns {Promise<File>} 压缩后的文件
 */
export function compressImage(file, options = {}) {
  const {
    maxWidth = 1920,
    maxHeight = 1920,
    quality = 0.8,
    maxSizeMB = 2
  } = options;

  return new Promise((resolve, reject) => {
    // 检查是否为图片文件
    if (!file.type.startsWith('image/')) {
      reject(new Error('文件不是图片类型'));
      return;
    }

    // 如果图片已经小于目标大小，直接返回
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size <= maxSizeBytes && !needsResize(file)) {
      resolve(file);
      return;
    }

    const reader = new FileReader();
    
    reader.onload = (e) => {
      const img = new Image();
      
      img.onload = () => {
        // 计算压缩后的尺寸
        const { width, height } = calculateSize(
          img.width,
          img.height,
          maxWidth,
          maxHeight
        );

        // 创建 canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = width;
        canvas.height = height;

        // 绘制图片
        ctx.drawImage(img, 0, 0, width, height);

        // 转换为 Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              // 检查压缩后的大小
              if (blob.size > maxSizeBytes && quality > 0.3) {
                // 如果还是太大，递归调用，降低质量
                const newQuality = quality - 0.1;
                console.log(`图片还是太大(${(blob.size / 1024 / 1024).toFixed(2)}MB)，降低质量到${newQuality}`);
                
                const tempFile = new File([blob], file.name, {
                  type: file.type,
                  lastModified: Date.now()
                });
                
                compressImage(tempFile, {
                  ...options,
                  quality: newQuality
                }).then(resolve).catch(reject);
              } else {
                // 创建新的 File 对象
                const compressedFile = new File([blob], file.name, {
                  type: file.type,
                  lastModified: Date.now()
                });

                console.log(`压缩完成: ${(file.size / 1024 / 1024).toFixed(2)}MB → ${(compressedFile.size / 1024 / 1024).toFixed(2)}MB`);
                resolve(compressedFile);
              }
            } else {
              reject(new Error('压缩失败'));
            }
          },
          file.type,
          quality
        );
      };

      img.onerror = () => {
        reject(new Error('图片加载失败'));
      };

      img.src = e.target.result;
    };

    reader.onerror = () => {
      reject(new Error('文件读取失败'));
    };

    reader.readAsDataURL(file);
  });
}

/**
 * 计算压缩后的尺寸
 * @param {number} originalWidth - 原始宽度
 * @param {number} originalHeight - 原始高度
 * @param {number} maxWidth - 最大宽度
 * @param {number} maxHeight - 最大高度
 * @returns {Object} 计算后的宽高
 */
function calculateSize(originalWidth, originalHeight, maxWidth, maxHeight) {
  let width = originalWidth;
  let height = originalHeight;

  // 如果宽度超过最大宽度
  if (width > maxWidth) {
    height = (maxWidth / width) * height;
    width = maxWidth;
  }

  // 如果高度超过最大高度
  if (height > maxHeight) {
    width = (maxHeight / height) * width;
    height = maxHeight;
  }

  return {
    width: Math.round(width),
    height: Math.round(height)
  };
}

/**
 * 检查是否需要调整大小
 * @param {File} file - 图片文件
 * @param {number} maxWidth - 最大宽度（未使用，预留）
 * @param {number} maxHeight - 最大高度（未使用，预留）
 * @returns {boolean} 是否需要调整
 */
function needsResize(file) {
  // 这里简单判断，实际可以读取图片尺寸
  // 对于大于 2MB 的图片，通常都需要压缩
  // 注：maxWidth 和 maxHeight 参数预留给未来可能的尺寸检查
  return file.size > 2 * 1024 * 1024;
}

/**
 * 批量压缩图片
 * @param {File[]} files - 图片文件数组
 * @param {Object} options - 压缩选项
 * @returns {Promise<File[]>} 压缩后的文件数组
 */
export function compressImages(files, options = {}) {
  const promises = files.map(file => {
    // 如果不是图片，直接返回
    if (!file.type.startsWith('image/')) {
      return Promise.resolve(file);
    }
    return compressImage(file, options).catch(err => {
      console.error('压缩图片失败:', file.name, err);
      // 压缩失败时返回原文件
      return file;
    });
  });

  return Promise.all(promises);
}

/**
 * 获取图片的实际尺寸
 * @param {File} file - 图片文件
 * @returns {Promise<{width: number, height: number}>} 图片尺寸
 */
export function getImageDimensions(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const img = new Image();
      
      img.onload = () => {
        resolve({
          width: img.width,
          height: img.height
        });
      };
      
      img.onerror = () => {
        reject(new Error('无法获取图片尺寸'));
      };
      
      img.src = e.target.result;
    };
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'));
    };
    
    reader.readAsDataURL(file);
  });
}

export default {
  compressImage,
  compressImages,
  getImageDimensions
};