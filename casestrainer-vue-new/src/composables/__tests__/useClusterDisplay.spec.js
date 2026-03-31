/**
 * Display helpers vs shared repo fixture (tests/fixtures/citation_display_shape.json).
 * Keeps canonical URL/name/year expectations aligned with Python brief_golden_expectations.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import {
  getClusterVerifyingUrl,
  getClusterVerifyingName,
  getCitationStatusClass,
  getCitationStatusText,
  formatCitationText,
} from '../useClusterDisplay.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const fixturePath = join(__dirname, '../../../../tests/fixtures/citation_display_shape.json')
const shape = JSON.parse(readFileSync(fixturePath, 'utf-8'))

describe('useClusterDisplay with citation_display_shape fixture', () => {
  it('exposes cluster-level verifying URL and name from API shape', () => {
    const cl = {
      ...shape.sample_cluster_verified,
      citations: [shape.sample_citation_verified_scotus],
    }
    expect(getClusterVerifyingUrl(cl)).toContain('courtlistener.com')
    expect(getClusterVerifyingName(cl)).toContain('Loper Bright')
  })

  it('formats citation text for the citation chip', () => {
    const t = formatCitationText(shape.sample_citation_verified_scotus)
    expect(t).toMatch(/606/)
    expect(t).toMatch(/831/)
  })

  it('marks cluster-verified citations as verified in UI status', () => {
    const isEff = () => false
    const isNa = () => false
    const cit = shape.sample_citation_verified_scotus
    const cluster = { verified: true, citations: [cit] }
    expect(getCitationStatusClass(cit, cluster, isEff, isNa)).toBe('status-verified')
    expect(getCitationStatusText(cit, cluster, isEff, isNa)).toBe('Verified')
  })

  it('matches golden canonical_year on sample citation', () => {
    expect(String(shape.sample_citation_verified_scotus.canonical_year)).toBe('2024')
  })
})
