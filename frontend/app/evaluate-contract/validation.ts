export const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx'] as const;
export const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

export function validateFileExtension(fileName: string): boolean {
  const dotIndex = fileName.lastIndexOf('.');
  if (dotIndex === -1) return false;
  const ext = fileName.slice(dotIndex).toLowerCase();
  return (ALLOWED_EXTENSIONS as readonly string[]).includes(ext);
}

export function validateFileSize(sizeInBytes: number): boolean {
  return sizeInBytes <= MAX_FILE_SIZE_BYTES;
}
