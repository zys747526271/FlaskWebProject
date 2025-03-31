import fernet from 'fernet';

/**
 * 使用Fernet加密数据
 * @param {string} data - 要加密的数据
 * @param {string} key - 加密密钥
 * @returns {string} - 加密后的数据
 */
export function encryptData(data, key) {
  if (!data) return null;
  
  // 确保输入数据是字符串类型
  const strData = String(data).trim();
  
  // 创建新的Fernet实例
  const secret = new fernet.Secret(key);
  const token = new fernet.Token({
    secret: secret,
    time: Date.now(),
    iv: undefined
  });
  
  // 加密数据
  return token.encode(strData);
}

/**
 * 解密数据
 * @param {string} encryptedData - 加密的数据
 * @param {string} key - 解密密钥
 * @returns {string} - 解密后的数据
 */
export function decryptData(encryptedData, key) {
  if (!encryptedData) return null;
  
  try {
    // 创建新的Fernet实例
    const secret = new fernet.Secret(key);
    const token = new fernet.Token({
      secret: secret,
      token: encryptedData,
      ttl: 0 // 不验证令牌时间
    });
    
    // 解密数据
    return token.decode();
  } catch (error) {
    console.error('解密失败:', error);
    return null;
  }
}