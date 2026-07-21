from m516.enrichment.port_risk import port_risk_label


def test_known_ports_return_label_and_description():
    label, description = port_risk_label(22, "tcp")
    assert label == "Weak Authentication"
    assert "brute-forc" in description.lower()

    label, _ = port_risk_label(3306, "tcp")
    assert label == "Open Database"

    label, _ = port_risk_label(3389, "tcp")
    assert label == "Exposed Remote Desktop"

    label, _ = port_risk_label(80, "tcp")
    assert label == "Unencrypted Traffic"


def test_admin_panel_ports_share_the_same_label():
    for port in (2077, 2078, 2079, 2080, 2082, 2083, 2086, 2087):
        label, _ = port_risk_label(port, "tcp")
        assert label == "Exposed Admin Panel"


def test_unknown_port_returns_none():
    assert port_risk_label(9, "tcp") is None
    assert port_risk_label(65000, "tcp") is None
