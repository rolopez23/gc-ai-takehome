export const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx'] as const;
export const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

export function validateFileExtension(fileName: string) {
  const dotIndex = fileName.lastIndexOf('.');
  if (dotIndex === -1) return false;
  const ext = fileName.slice(dotIndex).toLowerCase();
  return ALLOWED_EXTENSIONS.includes(ext as typeof ALLOWED_EXTENSIONS[number]);
}

export function validateFileSize(sizeInBytes: number) {
  return sizeInBytes <= MAX_FILE_SIZE_BYTES;
}
