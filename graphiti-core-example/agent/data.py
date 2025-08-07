from graphiti_core.nodes import EpisodeType

episodes = [
    {
        'content': "Dell Pro Max 14 Premium MA14250 Owner's Manual. Regulatory Model: P201G. Regulatory Type: P201G001. July 2025. Rev. A00.",
        'type': EpisodeType.text,
        'description': 'manual metadata',
    },
    {
        'content': (
            "A NOTE indicates important information that helps you make better use of your product. "
            "A CAUTION indicates potential hardware damage or data loss and how to avoid it. "
            "A WARNING indicates potential for property damage, personal injury, or death."
        ),
        'type': EpisodeType.text,
        'description': 'safety notes definitions',
    },
    {
        'content': {
            'model': 'Dell Pro Max 14 Premium MA14250',
            'regulatory_model': 'P201G',
            'regulatory_type': 'P201G001',
            'revision_date': 'July 2025',
            'revision': 'A00',
        },
        'type': EpisodeType.json,
        'description': 'manual metadata',
    },
    {
        'content': "Chapters: 1 Views (p. 7); 2 Set up (p. 13); 3 Specifications (p. 15); 4 Working inside (p. 31); 5 CRUs (p. 39); 6 FRUs (p. 60); 7 Software (p. 108); 8 BIOS (p. 109); 9 Troubleshooting (p. 134); 10 Contact (p. 140); 11 Revision history (p. 141).",
        'type': EpisodeType.text,
        'description': 'table of contents summary',
    },
    {
        'content': [
            {'chapter': 1, 'title': 'Views of Dell Pro Max 14 Premium MA14250', 'page': 7},
            {'chapter': 2, 'title': 'Set up your Dell Pro Max 14 Premium MA14250', 'page': 13},
            {'chapter': 3, 'title': 'Specifications of Dell Pro Max 14 Premium MA14250', 'page': 15},
            {'chapter': 4, 'title': 'Working inside your computer', 'page': 31},
            {'chapter': 5, 'title': 'Removing and installing Customer Replaceable Units (CRUs)', 'page': 39},
            {'chapter': 6, 'title': 'Removing and installing Field Replaceable Units (FRUs)', 'page': 60},
            {'chapter': 7, 'title': 'Software', 'page': 108},
            {'chapter': 8, 'title': 'BIOS Setup', 'page': 109},
            {'chapter': 9, 'title': 'Troubleshooting', 'page': 134},
            {'chapter': 10, 'title': 'Getting help and contacting Dell', 'page': 140},
            {'chapter': 11, 'title': 'Revision history', 'page': 141},
        ],
        'type': EpisodeType.json,
        'description': 'table of contents metadata',
    },
    {
        'content': "Right view ports and slots: microSD card slot; two Thunderbolt 4 (40 Gbps) with Power Delivery and DisplayPort 2.1; global headset port; security-cable slot.",
        'type': EpisodeType.text,
        'description': 'device right-side overview',
    },
    {
        'content': {
            'view': 'Right',
            'components': [
                {'position': 1, 'name': 'microSD card slot', 'details': 'Supports microSD, micro-SDHC, micro-SDXC cards.'},
                {'position': 2, 'name': 'Two Thunderbolt 4 ports', 'details': 'Up to 40 Gbps, Power Delivery, DisplayPort 2.1.'},
                {'position': 3, 'name': 'Global headset port', 'details': 'Headphone/microphone combo jack.'},
                {'position': 4, 'name': 'Security-cable slot', 'details': 'Connect a wedge-shaped lock to secure device.'},
            ],
        },
        'type': EpisodeType.json,
        'description': 'right-side port details',
    },
    {
        'content': "Left view ports: two Thunderbolt 5 (Up to 120 Gbps) with Power Delivery and DisplayPort 2.1; power & battery-status light.",
        'type': EpisodeType.text,
        'description': 'device left-side overview',
    },
    {
        'content': {
            'view': 'Left',
            'components': [
                {'position': 1, 'name': 'Two Thunderbolt 5 ports', 'details': 'Up to 120 Gbps, Power Delivery, DisplayPort 2.1.'},
                {'position': 2, 'name': 'Power & battery-status light', 'details': 'Indicates power or low battery via white/amber/off.'},
            ],
        },
        'type': EpisodeType.json,
        'description': 'left-side port details',
    },
    {
        'content': "Battery-status light behavior: AC adapter Off=100%; Solid white=<100%; Battery Off=11–100%; Solid amber=<10%.",
        'type': EpisodeType.text,
        'description': 'battery indicator guide',
    },
    {
        'content': {
            'battery_status_light': [
                {'power_source': 'AC adapter', 'LED': 'Off', 'state': 'S0 or S5', 'charge': '100%'},
                {'power_source': 'AC adapter', 'LED': 'Solid white', 'state': 'S0 or S5', 'charge': '<100%'},
                {'power_source': 'Battery', 'LED': 'Off', 'state': 'S0 or S5', 'charge': '11–100%'},
                {'power_source': 'Battery', 'LED': 'Solid amber', 'state': 'S0 or S5', 'charge': '<10%'},
            ],
        },
        'type': EpisodeType.json,
        'description': 'battery-status light table',
    },
    {
        'content': {
            'battery_options': {
                'option_one': {
                    'type': '4-cell, 72 Wh, ExpressCharge',
                    'voltage': '15.6 VDC',
                    'weight_max': '0.27 kg',
                    'dimensions_mm': {'height': 7.64, 'width': 266.62, 'depth': 72.68},
                    'temperature_C': {
                        'charge': '0–50',
                        'discharge': '0–60',
                        'storage': '-20–65'
                    }
                },
                'option_two': {
                    'type': '4-cell, 72 Wh, ExpressCharge, Long Life Cycle',
                    'voltage': '15.6 VDC',
                    'weight_max': '0.27 kg',
                    'dimensions_mm': {'height': 7.64, 'width': 266.62, 'depth': 72.68},
                    'temperature_C': {
                        'charge': '0–50',
                        'discharge': '0–60',
                        'storage': '-20–65'
                    }
                }
            }
        },
        'type': EpisodeType.json,
        'description': 'battery specifications',
    },
]
