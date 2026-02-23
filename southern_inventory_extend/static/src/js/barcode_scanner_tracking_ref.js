/** @odoo-module **/

import { StockBarcodePickingClientAction } from "@stock_barcode/stock_barcode_picking_client_action";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(StockBarcodePickingClientAction.prototype, {

    /**
     * Override the barcode scanned method to handle carrier tracking references
     */
    async _onBarcodeScanned(barcode) {
        const result = await this._super(...arguments);

        // If barcode wasn't processed by the standard handlers, check if it's a tracking reference
        if (!result.special && !result.match) {
            return this._handleTrackingReference(barcode);
        }

        return result;
    },

    /**
     * Handle tracking reference barcode scanning
     * Format: 12345678-1123453455335 (we only need the part before the dash)
     */
    _handleTrackingReference(barcode) {
        // Check if we're in the right context (outgoing picking with carrier_tracking_ref field visible)
        if (this.currentState.picking_type_code !== 'outgoing') {
            return { special: false, match: false };
        }

        // Check if the barcode matches the tracking reference format (contains a dash)
        const trackingMatch = barcode.match(/^([^-]+)-(.+)$/);
        if (!trackingMatch) {
            return { special: false, match: false };
        }

        // Extract the tracking number (part before the dash)
        const trackingNumber = trackingMatch[1];

        // Check if the carrier_tracking_ref field is present and can be updated
        if (this._canUpdateTrackingRef()) {
            return this._updateTrackingRef(trackingNumber);
        }

        return { special: false, match: false };
    },

    /**
     * Check if we can update the tracking reference field
     */
    _canUpdateTrackingRef() {
        // Check if the picking is in a state where tracking ref can be updated
        const picking = this.currentState;
        return picking &&
               picking.picking_type_code === 'outgoing' &&
               ['draft', 'waiting', 'confirmed', 'assigned'].includes(picking.state);
    },

    /**
     * Update the carrier tracking reference field
     */
    async _updateTrackingRef(trackingNumber) {
        try {
            // Update the tracking reference in the backend
            await this.orm.write('stock.picking', [this.currentState.id], {
                carrier_tracking_ref: trackingNumber
            });

            // Update the current state to reflect the change
            this.currentState.carrier_tracking_ref = trackingNumber;

            // Trigger a re-render to show the updated field
            this.render();

            // Show success notification
            this.notification.add(
                _t('Tracking reference updated: %s', trackingNumber),
                { type: 'success' }
            );

            return {
                special: true,
                match: true,
                message: _t('Tracking reference set to: %s', trackingNumber)
            };

        } catch (error) {
            console.error('Error updating tracking reference:', error);

            this.notification.add(
                _t('Error updating tracking reference'),
                { type: 'danger' }
            );

            return { special: false, match: false };
        }
    },

    /**
     * Override to handle special case where user scans tracking ref when field is focused
     */
    async _processBarcode(barcode) {
        // Check if the carrier_tracking_ref field is currently focused
        const focusedElement = document.activeElement;
        if (focusedElement &&
            focusedElement.name === 'carrier_tracking_ref' &&
            barcode.includes('-')) {

            // Extract tracking number and populate the field
            const trackingNumber = barcode.split('-')[0];
            focusedElement.value = trackingNumber;

            // Trigger change event to update the model
            focusedElement.dispatchEvent(new Event('change', { bubbles: true }));

            return { special: true, match: true };
        }

        return await this._super(...arguments);
    }
});