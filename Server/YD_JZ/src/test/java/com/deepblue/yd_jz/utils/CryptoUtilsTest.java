package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.exception.BusinessException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

// v2.7.0 (config-ui): CryptoUtils 单测
// 覆盖：默认密钥往返 / 自定义密钥往返 / null 透传 / 空串透传 / 特殊字符 /
//      非法密文抛 BusinessException / 错密钥解密抛 BusinessException /
//      同明文加密两次得到不同密文（IV 随机性）
class CryptoUtilsTest {

    @Test
    void encryptThenDecrypt_default_roundTrip() {
        String plain = "my-smtp-password-123!@#";
        String cipher = CryptoUtils.aesEncrypt(plain);
        assertNotNull(cipher);
        assertNotEquals(plain, cipher);
        assertEquals(plain, CryptoUtils.aesDecrypt(cipher));
    }

    @Test
    void encryptThenDecrypt_customKey_roundTrip() {
        String plain = "any-secret";
        String cipher = CryptoUtils.aesEncrypt(plain, "another-key");
        assertEquals(plain, CryptoUtils.aesDecrypt(cipher, "another-key"));
    }

    @Test
    void nullInput_passthrough() {
        assertNull(CryptoUtils.aesEncrypt(null));
        assertNull(CryptoUtils.aesDecrypt(null));
    }

    @Test
    void emptyDecrypt_passthrough() {
        // 空串视为"未配置"，解密时直接透传
        assertEquals("", CryptoUtils.aesDecrypt(""));
    }

    @Test
    void emptyPlain_canEncryptAndDecrypt() {
        // 空明文也能正常加解密（业务上一般用 "" 表示未配置，不应进入加密路径，
        // 但工具层不主动拦，给上层自己决定）
        String cipher = CryptoUtils.aesEncrypt("");
        assertNotNull(cipher);
        assertEquals("", CryptoUtils.aesDecrypt(cipher));
    }

    @Test
    void specialChars_chineseAndSymbols() {
        String plain = "密码🔒 ~!@#$%^&*()_+ 中文混合";
        String cipher = CryptoUtils.aesEncrypt(plain);
        assertEquals(plain, CryptoUtils.aesDecrypt(cipher));
    }

    @Test
    void sameInput_differentCiphers_dueToRandomIv() {
        String plain = "same-input";
        String c1 = CryptoUtils.aesEncrypt(plain);
        String c2 = CryptoUtils.aesEncrypt(plain);
        assertNotEquals(c1, c2, "随机 IV 应使两次加密结果不同");
        assertEquals(plain, CryptoUtils.aesDecrypt(c1));
        assertEquals(plain, CryptoUtils.aesDecrypt(c2));
    }

    @Test
    void invalidCipher_tooShort_throwsBusinessException() {
        // 长度 < 16 字节（IV 长度），无法切分
        String fakeShort = java.util.Base64.getEncoder().encodeToString(new byte[]{1, 2, 3});
        assertThrows(BusinessException.class, () -> CryptoUtils.aesDecrypt(fakeShort));
    }

    @Test
    void invalidCipher_garbageBase64_throwsBusinessException() {
        assertThrows(BusinessException.class, () -> CryptoUtils.aesDecrypt("not-valid-base64-!!!"));
    }

    @Test
    void wrongKey_decryptFails() {
        String cipher = CryptoUtils.aesEncrypt("secret", "key-A");
        assertThrows(BusinessException.class, () -> CryptoUtils.aesDecrypt(cipher, "key-B"));
    }
}
