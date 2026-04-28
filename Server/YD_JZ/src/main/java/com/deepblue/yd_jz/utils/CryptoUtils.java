package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import lombok.extern.slf4j.Slf4j;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;

// v2.7.0 (config-ui): AES 对称加密工具
// 用途：app_config.mail.password 等敏感字段密文入库，避免 DB 导出时密码明文外泄
// 算法：AES-256/CBC/PKCS5Padding；密钥由 SHA-256(passphrase) 派生为 32 字节
// 入库格式：Base64(IV(16 bytes) || ciphertext)
@Slf4j
public class CryptoUtils {

    private static final String CIPHER_ALGO = "AES/CBC/PKCS5Padding";
    private static final String DEFAULT_PASSPHRASE = "easyaccounts";
    private static final int IV_LEN = 16;
    private static final SecureRandom RNG = new SecureRandom();

    private CryptoUtils() {}

    /** 默认密钥加密（项目级密钥 = "easyaccounts"） */
    public static String aesEncrypt(String plain) {
        return aesEncrypt(plain, DEFAULT_PASSPHRASE);
    }

    /** 默认密钥解密 */
    public static String aesDecrypt(String cipherBase64) {
        return aesDecrypt(cipherBase64, DEFAULT_PASSPHRASE);
    }

    /** 加密：明文 → Base64(IV || ciphertext)；null 透传，空串原样加密 */
    public static String aesEncrypt(String plain, String passphrase) {
        if (plain == null) return null;
        try {
            byte[] iv = new byte[IV_LEN];
            RNG.nextBytes(iv);

            Cipher cipher = Cipher.getInstance(CIPHER_ALGO);
            cipher.init(Cipher.ENCRYPT_MODE, deriveKey(passphrase), new IvParameterSpec(iv));
            byte[] cipherBytes = cipher.doFinal(plain.getBytes(StandardCharsets.UTF_8));

            byte[] combined = new byte[IV_LEN + cipherBytes.length];
            System.arraycopy(iv, 0, combined, 0, IV_LEN);
            System.arraycopy(cipherBytes, 0, combined, IV_LEN, cipherBytes.length);

            return Base64.getEncoder().encodeToString(combined);
        } catch (Exception e) {
            log.error("AES encrypt failed: {}", e.getMessage());
            throw new BusinessException(ErrorCode.CRYPTO_FAILED, "加密失败");
        }
    }

    /** 解密：Base64(IV || ciphertext) → 明文；null/空串透传（视为未配置） */
    public static String aesDecrypt(String cipherBase64, String passphrase) {
        if (cipherBase64 == null || cipherBase64.isEmpty()) return cipherBase64;
        try {
            byte[] combined = Base64.getDecoder().decode(cipherBase64);
            if (combined.length <= IV_LEN) {
                throw new BusinessException(ErrorCode.CRYPTO_FAILED, "密文长度异常");
            }
            byte[] iv = new byte[IV_LEN];
            byte[] cipherBytes = new byte[combined.length - IV_LEN];
            System.arraycopy(combined, 0, iv, 0, IV_LEN);
            System.arraycopy(combined, IV_LEN, cipherBytes, 0, cipherBytes.length);

            Cipher cipher = Cipher.getInstance(CIPHER_ALGO);
            cipher.init(Cipher.DECRYPT_MODE, deriveKey(passphrase), new IvParameterSpec(iv));
            byte[] plainBytes = cipher.doFinal(cipherBytes);
            return new String(plainBytes, StandardCharsets.UTF_8);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("AES decrypt failed: {}", e.getMessage());
            throw new BusinessException(ErrorCode.CRYPTO_FAILED, "解密失败");
        }
    }

    // SHA-256(passphrase) → 32 字节，作为 AES-256 密钥
    private static SecretKeySpec deriveKey(String passphrase) {
        try {
            MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
            byte[] keyBytes = sha256.digest(passphrase.getBytes(StandardCharsets.UTF_8));
            return new SecretKeySpec(keyBytes, "AES");
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.CRYPTO_FAILED, "密钥派生失败");
        }
    }
}
