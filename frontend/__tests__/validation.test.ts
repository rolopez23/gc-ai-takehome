import { describe, it, expect } from 'vitest';
import {
  validateFileExtension,
  validateFileSize,
} from '@/app/evaluate-contract/validation';

describe('validateFileExtension', () => {
  it('accepts .txt files', () => {
    expect(validateFileExtension('contract.txt')).toBe(true);
  });

  it('rejects .pdf files', () => {
    expect(validateFileExtension('contract.pdf')).toBe(false);
  });

  it('rejects .doc files', () => {
    expect(validateFileExtension('contract.doc')).toBe(false);
  });

  it('rejects .docx files', () => {
    expect(validateFileExtension('contract.docx')).toBe(false);
  });

  it('rejects .png files', () => {
    expect(validateFileExtension('image.png')).toBe(false);
  });

  it('rejects files with no extension', () => {
    expect(validateFileExtension('README')).toBe(false);
  });

  it('is case-insensitive', () => {
    expect(validateFileExtension('CONTRACT.TXT')).toBe(true);
  });

  it('checks the last extension only', () => {
    expect(validateFileExtension('file.tar.txt')).toBe(true);
    expect(validateFileExtension('file.txt.exe')).toBe(false);
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

