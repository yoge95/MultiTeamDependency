import { describe, it, expect } from 'vitest';
import { cn, formatCurrency, formatDateTime, formatRelativeTime, getStatusBadgeColor } from '../src/lib/utils';

describe('utils', () => {
  describe('cn', () => {
    it('should merge class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('should handle conditional classes', () => {
      expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
    });
  });

  describe('formatCurrency', () => {
    it('should format currency with default USD', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
    });

    it('should format currency with custom currency', () => {
      expect(formatCurrency(1234.56, 'EUR')).toMatch(/1,234\.56/);
    });
  });

  describe('formatDateTime', () => {
    it('should format ISO datetime', () => {
      const result = formatDateTime('2024-01-15T10:30:00Z');
      expect(result).toContain('Jan');
      expect(result).toContain('15');
    });
  });

  describe('formatRelativeTime', () => {
    it('should format recent time as "just now"', () => {
      const now = new Date().toISOString();
      expect(formatRelativeTime(now)).toBe('just now');
    });

    it('should format minutes ago', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      expect(formatRelativeTime(fiveMinutesAgo)).toBe('5m ago');
    });

    it('should format hours ago', () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();
      expect(formatRelativeTime(threeHoursAgo)).toBe('3h ago');
    });

    it('should format days ago', () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
      expect(formatRelativeTime(twoDaysAgo)).toBe('2d ago');
    });
  });

  describe('getStatusBadgeColor', () => {
    it('should return yellow for processing status', () => {
      expect(getStatusBadgeColor('processing')).toContain('yellow');
    });

    it('should return green for completed status', () => {
      expect(getStatusBadgeColor('completed')).toContain('green');
    });

    it('should return red for error status', () => {
      expect(getStatusBadgeColor('error')).toContain('red');
    });

    it('should return orange for warning status', () => {
      expect(getStatusBadgeColor('warning')).toContain('orange');
    });

    it('should return gray for unknown status', () => {
      expect(getStatusBadgeColor('unknown')).toContain('gray');
    });
  });
});
