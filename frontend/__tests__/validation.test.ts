import { describe, it, expect } from 'vitest';
import {
  validateFileExtension,
  validateFileSize,
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
} from '@/app/evaluate-contract/validation';

describe('validateFileExtension', () => {
  it('accepts .pdf files', () => {
    expect(validateFileExtension('contract.pdf')).toBe(true);
  });

  it('accepts .txt files', () => {
    expect(validateFileExtension('contract.txt')).toBe(true);
  });

  it('accepts .doc files', () => {
    expect(validateFileExtension('contract.doc')).toBe(true);
  });

  it('accepts .docx files', () => {
    expect(validateFileExtension('contract.docx')).toBe(true);
  });

  it('rejects .png files', () => {
    expect(validateFileExtension('image.png')).toBe(false);
  });

  it('rejects files with no extension', () => {
    expect(validateFileExtension('README')).toBe(false);
  });

  it('is case-insensitive', () => {
    expect(validateFileExtension('CONTRACT.PDF')).toBe(true);
  });

  it('checks the last extension only', () => {
    expect(validateFileExtension('file.tar.pdf')).toBe(true);
    expect(validateFileExtension('file.pdf.exe')).toBe(false);
  });
});

describe('ALLOWED_EXTENSIONS', () => {
  it('contains exactly .pdf, .txt, .doc, .docx', () => {
    expect([...ALLOWED_EXTENSIONS]).toEqual(['.pdf', '.txt', '.doc', '.docx']);
  });
});

describe('validateFileSize', () => {
  it('accepts files under 5 MB', () => {
    expect(validateFileSize(1024)).toBe(true);
  });

  it('accepts files exactly at 5 MB', () => {
    expect(validateFileSize(5 * 1024 * 1024)).toBe(true);
  });

  it('rejects files over 5 MB', () => {
    expect(validateFileSize(5 * 1024 * 1024 + 1)).toBe(false);
  });

  it('accepts zero-byte files', () => {
    expect(validateFileSize(0)).toBe(true);
  });
});

describe('MAX_FILE_SIZE_BYTES', () => {
  it('is 5 MB', () => {
    expect(MAX_FILE_SIZE_BYTES).toBe(5 * 1024 * 1024);
  });
});
