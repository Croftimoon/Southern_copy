/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { jsonrpc } from "@web/core/network/rpc_service";

export class SpreadsheetColumnDropdown extends Component {
    static template = "southern_stock_import.SpreadsheetColumnDropdown";
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
    };

    setup() {
        this.selectRef = useRef("select");
        this.state = useState({
            options: [],
            isLoading: false,
            hasLoaded: false
        });

        onMounted(() => {
            this.loadOptionsIfFileExists();
        });
    }

    async loadOptionsIfFileExists() {
        const record = this.props.record;
        const fileData = record.data.file_data;
        const fileName = record.data.file_name;

        if (!fileData || !fileName || this.state.hasLoaded) {
            return;
        }

        this.state.isLoading = true;

        try {
            const result = await jsonrpc('/web/dataset/call_kw', {
                model: 'spreadsheet.import.wizard',
                method: 'parse_file_preview',
                args: [],
                kwargs: {
                    file_data: fileData,
                    file_name: fileName
                }
            });

            if (result.success) {
                this.state.options = result.column_options || [];
                this.state.hasLoaded = true;

                // Update preview for first field only
                if (result.preview_html && this.props.name === 'product_column_index') {
                    this.updatePreview(result.preview_html);
                }
            } else {
                this.state.options = [];
                this.showError(result.error);
            }
        } catch (error) {
            console.error('Error loading column options:', error);
            this.state.options = [];
        } finally {
            this.state.isLoading = false;
        }
    }

    updatePreview(previewHtml) {
        setTimeout(() => {
            const previewContainers = document.querySelectorAll('[name="first_row_preview"]');
            previewContainers.forEach(container => {
                let previewDiv = container.querySelector('.o_field_widget');
                if (!previewDiv) {
                    previewDiv = container;
                }
                if (previewDiv) {
                    previewDiv.innerHTML = previewHtml;
                }
            });
        }, 100);
    }

    showError(message) {
        setTimeout(() => {
            const previewContainers = document.querySelectorAll('[name="first_row_preview"]');
            previewContainers.forEach(container => {
                let previewDiv = container.querySelector('.o_field_widget');
                if (!previewDiv) {
                    previewDiv = container;
                }
                if (previewDiv) {
                    previewDiv.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            <strong>Error:</strong> ${message}
                        </div>
                    `;
                }
            });
        }, 100);
    }

    get currentValue() {
        return this.props.record.data[this.props.name] || '';
    }

    get placeholderText() {
        if (this.state.isLoading) {
            return "Loading columns...";
        }
        if (this.state.options.length === 0) {
            return "Upload file to see columns";
        }
        return this.props.placeholder || "Select Column";
    }

    onChange(ev) {
        const value = ev.target.value;
        this.props.record.update({ [this.props.name]: value });
    }
}

// Proper field widget registration for Odoo 17
registry.category("fields").add("spreadsheet_column_dropdown", {
    component: SpreadsheetColumnDropdown,
    supportedTypes: ["char"],
    extractProps: ({ options }) => ({
        placeholder: options?.placeholder,
    }),
});