/**
 * 图片压缩工具
 * 用于在上传前压缩图片，减少上传时间和服务器存储空间
 */

interface CompressOptions {
  maxWidth?: number
  maxHeight?: number
  quality?: number
  maxSizeMB?: number
}

/**
 * 压缩图片
 * @param file - 原始图片文件
 * @param options - 压缩选项
 * @returns 压缩后的文件
 */
export function compressImage(file: File, options: CompressOptions = {}): Promise<File> {
  const {
    maxWidth = 1920,
    maxHeight = 1920,
    quality = 0.8,
    maxSizeMB = 2
  } = options

  return new Promise((resolve, reject) => {
    // 检查是否为图片文件
    if (!file.type.startsWith('image/')) {
      reject(new Error('文件不是图片类型'))
      return
    }

    // 如果图片已经小于目标大小，直接返回
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    if (file.size <= maxSizeBytes && file.size <= 2 * 1024 * 1024) {
      resolve(file)
      return
    }

    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        // 计算压缩后的尺寸
        const { width, height } = calculateSize(
          img.width,
          img.height,
          maxWidth,
          maxHeight
        )

        // 创建 canvas
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')

        if (!ctx) {
          reject(new Error('无法创建 canvas context'))
          return
        }

        canvas.width = width
        canvas.height = height

        // 绘制图片
        ctx.drawImage(img, 0, 0, width, height)

        // 转换为 Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              // 检查压缩后的大小
              if (blob.size > maxSizeBytes && quality > 0.3) {
                // 如果还是太大，递归调用，降低质量
                const newQuality = quality - 0.1
                console.log(`图片还是太大(${(blob.size / 1024 / 1024).toFixed(2)}MB)，降低质量到${newQuality}`)

                const tempFile = new File([blob], file.name, {
                  type: file.type,
                  lastModified: Date.now()
                })

                compressImage(tempFile, {
                  ...options,
                  quality: newQuality
                }).then(resolve).catch(reject)
              } else {
                // 创建新的 File 对象
                const compressedFile = new File([blob], file.name, {
                  type: file.type,
                  lastModified: Date.now()
                })

                console.log(`压缩完成: ${(file.size / 1024 / 1024).toFixed(2)}MB → ${(compressedFile.size / 1024 / 1024).toFixed(2)}MB`)
                resolve(compressedFile)
              }
            } else {
              reject(new Error('压缩失败'))
            }
          },
          file.type,
          quality
        )
      }

      img.onerror = () => {
        reject(new Error('图片加载失败'))
      }

      img.src = e.target?.result as string
    }

    reader.onerror = () => {
      reject(new Error('文件读取失败'))
    }

    reader.readAsDataURL(file)
  })
}

/**
 * 计算压缩后的尺寸
 */
function calculateSize(
  originalWidth: number,
  originalHeight: number,
  maxWidth: number,
  maxHeight: number
): { width: number; height: number } {
  let width = originalWidth
  let height = originalHeight

  // 如果宽度超过最大宽度
  if (width > maxWidth) {
    height = (maxWidth / width) * height
    width = maxWidth
  }

  // 如果高度超过最大高度
  if (height > maxHeight) {
    width = (maxHeight / height) * width
    height = maxHeight
  }

  return {
    width: Math.round(width),
    height: Math.round(height)
  }
}

/**
 * 批量压缩图片
 */
export function compressImages(files: File[], options: CompressOptions = {}): Promise<File[]> {
  const promises = files.map(file => {
    if (!file.type.startsWith('image/')) {
      return Promise.resolve(file)
    }
    return compressImage(file, options).catch(err => {
      console.error('压缩图片失败:', file.name, err)
      return file
    })
  })

  return Promise.all(promises)
}
