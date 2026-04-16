/**
 * Blostem Pragma API Client
 * Handles all communication with the backend REST API for WHO/WHEN/HOW/ACTIVATE layers
 */

class PragmaAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    /**
     * Generic fetch wrapper with error handling
     */
    async request(method, endpoint, data = null) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Request Failed (${method} ${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * GET /api/activate/patterns/all/summary
     * Returns dashboard summary: stalls, risks, metrics
     */
    async getDashboardSummary() {
        return this.request('GET', '/api/activate/patterns/all/summary');
    }

    /**
     * GET /api/activate/patterns/{partner_id}
     * Returns detected stalls for a specific partner
     */
    async getPartnerPatterns(partnerId) {
        return this.request('GET', `/api/activate/patterns/${partnerId}`);
    }

    /**
     * POST /api/activate/patterns/{partner_id}/generate-intervention
     * Generates intervention email based on stall pattern
     */
    async generateIntervention(partnerId, stallPattern, resolution = null) {
        return this.request('POST', `/api/activate/patterns/${partnerId}/generate-intervention`, {
            pattern: stallPattern,
            resolution: resolution,
        });
    }

    /**
     * POST /api/activate/patterns/{partner_id}/mark-intervention-sent
     * Logs that an intervention email was sent
     */
    async markInterventionSent(partnerId) {
        return this.request('POST', `/api/activate/patterns/${partnerId}/mark-intervention-sent`, {});
    }

    /**
     * POST /api/activate/patterns/{partner_id}/mark-resolved
     * Logs that a stall was resolved
     */
    async markStallResolved(partnerId, stallPattern) {
        return this.request('POST', `/api/activate/patterns/${partnerId}/mark-resolved`, {
            pattern: stallPattern,
        });
    }

    /**
     * GET /api/activate/partners/{partner_id}/contacts
     * Returns contacts for a partner, grouped by persona
     */
    async getPartnerContacts(partnerId) {
        return this.request('GET', `/api/activate/partners/${partnerId}/contacts`);
    }

    /**
     * POST /api/activate/partners/{partner_id}/contacts
     * Adds a new contact for a partner
     */
    async addPartnerContact(partnerId, name, email, persona, addedBy = 'system') {
        return this.request('POST', `/api/activate/partners/${partnerId}/contacts`, {
            name,
            email,
            persona,
            added_by: addedBy,
        });
    }

    /**
     * POST /api/activate/partners/{partner_id}/intervention-outcome
     * Records the outcome of an intervention
     */
    async recordInterventionOutcome(partnerId, stallPattern, outcome, sentToEmail = null, notes = null) {
        return this.request('POST', `/api/activate/partners/${partnerId}/intervention-outcome`, {
            stall_pattern: stallPattern,
            outcome,
            sent_to_email: sentToEmail,
            notes,
        });
    }

    /**
     * GET /api/activate/interventions/metrics
     * Returns effectiveness metrics by pattern
     */
    async getInterventionMetrics() {
        return this.request('GET', '/api/activate/interventions/metrics');
    }

    /**
     * GET /api/activate/political-risks/{partner_id}
     * Returns detected political risks for a partner
     */
    async getPartnerRisks(partnerId) {
        return this.request('GET', `/api/activate/political-risks/${partnerId}`);
    }

    /**
     * POST /api/activate/political-risks/{partner_id}/alert-sent
     * Logs that a political risk alert was sent
     */
    async markRiskAlertSent(partnerId) {
        return this.request('POST', `/api/activate/political-risks/${partnerId}/alert-sent`, {});
    }

    // ====== WHO LAYER: Prospect Discovery ======

    /**
     * GET /api/prospects
     * Returns all prospects with optional filtering
     */
    async getProspects(status = null, limit = 50) {
        let endpoint = `/api/prospects?limit=${limit}`;
        if (status) {
            endpoint += `&status=${status}`;
        }
        return this.request('GET', endpoint);
    }

    /**
     * GET /api/prospects/{prospect_id}
     * Returns full details for one prospect
     */
    async getProspectDetail(prospectId) {
        return this.request('GET', `/api/prospects/${prospectId}`);
    }

    /**
     * GET /api/stats
     * Returns dashboard stats for WHO layer
     */
    async getStats() {
        return this.request('GET', '/api/stats');
    }

    // ====== WHEN LAYER: Temporal Scoring ======

    /**
     * GET /api/when/priorities
     * Returns this week's priority list with action items
     */
    async getWhenPriorities() {
        return this.request('GET', '/api/when/priorities');
    }

    /**
     * GET /api/when/scores
     * Returns WHEN scores for all prospects
     */
    async getWhenScores() {
        return this.request('GET', '/api/when/scores');
    }

    /**
     * GET /api/when/{prospect_id}
     * Returns detailed WHEN score for one prospect
     */
    async getProspectWhen(prospectId) {
        return this.request('GET', `/api/when/${prospectId}`);
    }

    // ====== HOW LAYER: Outreach Generation ======

    /**
     * POST /api/how/generate/{prospect_id}
     * Generates complete outreach package with 3 persona emails
     */
    async generateOutreachPackage(prospectId) {
        return this.request('POST', `/api/how/generate/${prospectId}`);
    }

    /**
     * GET /api/how/packages
     * Lists all generated outreach packages
     */
    async getOutreachPackages() {
        return this.request('GET', '/api/how/packages');
    }

    /**
     * POST /api/prospects/{prospect_id}/mark-contacted
     * Records outreach interaction for a prospect
     */
    async markProspectContacted(prospectId, interactionType = 'EMAIL', emailPersona = null) {
        return this.request('POST', `/api/prospects/${prospectId}/mark-contacted`, {
            interaction_type: interactionType,
            email_persona: emailPersona,
        });
    }

    /**
     * GET /api/prospects/{prospect_id}/interaction-history
     * Returns full interaction history for a prospect
     */
    async getProspectInteractionHistory(prospectId) {
        return this.request('GET', `/api/prospects/${prospectId}/interaction-history`);
    }

    // ====== REVENUE PROOF ======

    /**
     * GET /api/activate/partners/{partner_id}/revenue-proof
     * Calculates revenue proof for a partner
     */
    async getRevenueProof(partnerId) {
        return this.request('GET', `/api/activate/partners/${partnerId}/revenue-proof`);
    }

    /**
     * GET /api/activate/demo/revenue-proof
     * Returns demo revenue calculation for Groww
     */
    async getDemoRevenueProof() {
        return this.request('GET', '/api/activate/demo/revenue-proof');
    }
}

// Export for use in pages
const api = new PragmaAPIClient();
