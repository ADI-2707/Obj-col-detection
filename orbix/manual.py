import os
import sys
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from orbix import __version__
from orbix.paths import get_resource_path


def get_manual_pdf_path() -> Path:
    target_dir = Path("data/docs")
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "Orbix_Features_and_Operation_Manual.pdf"


def draw_page_watermark_and_chrome(canvas, doc, logo_path: Path):
    canvas.saveState()
    w, h = doc.pagesize

    if logo_path.exists():
        try:
            wm_w = 4.2 * inch
            wm_h = 2.1 * inch
            canvas.setFillAlpha(0.08)
            canvas.drawImage(
                str(logo_path),
                (w - wm_w) / 2.0,
                (h - wm_h) / 2.0,
                width=wm_w,
                height=wm_h,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception:
            pass

    canvas.setStrokeColor(HexColor("#cbd5e1"))
    canvas.setLineWidth(0.6)
    canvas.line(36, h - 36, w - 36, h - 36)
    canvas.line(36, 40, w - 36, 40)

    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(HexColor("#475569"))
    canvas.drawString(36, h - 30, "ORBIX HOT METAL SLAB VISION SYSTEM — OPERATOR & FEATURE MANUAL")
    canvas.drawRightString(w - 36, h - 30, "SYSTROL AUTOMATION")

    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(36, 28, "CONFIDENTIAL & PROPRIETARY — FOR MILL AUTHORIZED PERSONNEL ONLY")
    page_num = canvas.getPageNumber()
    canvas.drawRightString(w - 36, 28, f"Page {page_num}")

    canvas.restoreState()


def generate_features_manual_pdf(output_path: Path | None = None) -> Path:
    if output_path is None:
        output_path = get_manual_pdf_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logo_path = get_resource_path("orbix/web/systrol_logo.png")
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "web" / "systrol_logo.png"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    c_primary = HexColor("#0f172a")
    c_blue = HexColor("#0284c7")
    c_sub = HexColor("#334155")
    c_muted = HexColor("#64748b")
    c_bg_head = HexColor("#f1f5f9")
    c_border = HexColor("#cbd5e1")

    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=c_primary,
        alignment=0,
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_muted,
        alignment=0,
    )
    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=c_blue,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "BodyOffice",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_sub,
        spaceAfter=4,
    )
    style_table_head = ParagraphStyle(
        "THead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=c_primary,
    )
    style_table_cell = ParagraphStyle(
        "TCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=c_sub,
    )
    style_badge = ParagraphStyle(
        "TBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=HexColor("#0369a1"),
    )

    story = []

    story.append(Paragraph("ORBIX VISION SYSTEM — FEATURES &amp; OPERATION MANUAL", style_title))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            f"Systrol Industrial Vision Software Suite &bull; Non-Contact Optical Slab Thickness Gauging &bull; Version {__version__}",
            style_subtitle,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=8))

    intro_p1 = (
        "This manual details all operating features, controls, and calibration routines of the Orbix "
        "Vision System. Each feature is mapped directly to its respective physical area on the user interface: "
        "<b>Top Bar</b>, <b>Left Sidebar</b>, <b>Center Viewport</b>, <b>Right Sidebar</b>, and <b>Bottom Profile Bar</b>. "
        "Use this reference to locate the required buttons, headings, and controls across the SCADA environment."
    )
    story.append(Paragraph(intro_p1, style_body))
    story.append(Spacer(1, 4 * mm))

    sections_data = [
        (
            "1. TOP BAR (GLOBAL SYSTEM CONTROLS & STATUS)",
            "Located at the uppermost header across the full application width.",
            [
                ("Settings Dropdown", "Top Right: Gear Icon (&#9881;)", "Click the gear icon to reveal the application configuration menu containing the Theme toggle, Help & Documentation modal, and About System modal."),
                ("Dark / Light Theme Toggle", "Inside Settings Menu: Switch Slider", "Toggle the slider switch between Dark Industrial mode and High-Contrast Light mode. Theme preference is preserved across restarts."),
                ("Help & Documentation", "Inside Settings Menu: 'Help & Documentation'", "Opens the on-screen feature manual detailing all software capabilities and provides a one-click button to launch this printable PDF manual."),
                ("About System Info", "Inside Settings Menu: 'About System'", f"Displays the vision engine build version (v{__version__}), Python 3.14 / Webview runtime architecture, and continuous casting mill specifications."),
                ("Live Stream Status Pill", "Top Right Header: 'VIDEO PLAYING'", "Displays real-time sensor connection health. Green indicates active video feed; amber indicates video pause; red indicates signal loss."),
                ("Quality Spec Status Pill", "Top Right Header: 'NORMAL' / 'OUT OF SPEC'", "Instant visual annunciator. Displays green NORMAL when slab thickness is within mill tolerance, or flashing red OUT OF SPEC when limits are violated."),
                ("DVR Recording Badge", "Top Right Header: 'RECORDING OFF' / 'REC ON'", "Click directly on this badge to start or stop real-time MJPEG video recording to disk (data/recordings/). Flashes red when recording."),
                ("Digital Mill Clock", "Top Center Header: HH:MM:SS", "Displays synchronized 24-hour plant workstation time accurate to the nearest second."),
            ],
        ),
        (
            "2. LEFT PANEL (INGESTION, REGION OF INTEREST & FILTERING)",
            "Houses video input feeds, spatial constraints, and optical thresholding parameters.",
            [
                ("RTSP / Camera IP Input", "IMAGE SOURCE: Text Input Field", "Enter the target sensor address: use '0' or '1' for local webcams/USB sensors, or enter RTSP URLs (e.g., rtsp://192.168.1.250:554/live/ch0)."),
                ("Connect Camera Button", "IMAGE SOURCE: [CONNECT CAMERA]", "Initiates hardware video capture for the specified camera index or RTSP network stream."),
                ("Open Video Dialog", "IMAGE SOURCE: [OPEN VIDEO]", "Opens native Windows file browser dialog to load recorded mill MP4/AVI/MKV test reel footage."),
                ("Open Image Dialog", "IMAGE SOURCE: [OPEN IMAGE]", "Opens file browser to load single-frame still images (JPG/PNG/BMP) for offline calibration and testing."),
                ("Sample Media Buttons", "IMAGE SOURCE: [SAMPLE IMAGE] & [SAMPLE VIDEO]", "Loads pre-bundled factory rolling mill hot slab test footage for bench demonstration without live cameras."),
                ("Select ROI Engine", "REGION OF INTEREST: [SELECT ROI]", "Click to enter interactive canvas selection mode. Click and drag across the video canvas to define a new bounding search window."),
                ("Confirm ROI Button", "REGION OF INTEREST: [CONFIRM ROI]", "Locks the newly drawn Region of Interest and synchronizes coordinates with the vision measurement engine."),
                ("Full Canvas ROI", "REGION OF INTEREST: [FULL]", "Instantly resets the inspection window to the full 1920x1080 sensor field of view."),
                ("Delete / Add Preset ROI", "REGION OF INTEREST: [DELETE] & [+ ADD]", "Delete clears constraints to full canvas; + Add applies standard 1440x810 centered mill preset boundaries."),
                ("Show/Hide ROI Box Eye", "REGION OF INTEREST Header: Eye Icon (&#128065;)", "Toggles visibility of the slate-gray dashed search window overlay on the video canvas without altering tracking."),
                ("Colour Space Selector", "THRESHOLD & DETECTION: 'COLOUR SPACE' Dropdown", "Select between Grayscale (cold slabs), HSV Value (hot glowing red slabs), and CIELAB Lightness (descaler water/glare suppression)."),
                ("Threshold Mode Selector", "THRESHOLD & DETECTION: 'THRESHOLD MODE' Dropdown", "Select between Otsu (automatic adaptive global thresholding), Adaptive Gaussian (local gradient), or Manual slider."),
                ("Spatial Blur Kernel", "THRESHOLD & DETECTION: 'BLUR / KERNEL'", "Applies spatial Gaussian convolution smoothing (k=5) to eliminate airborne steam, sparks, and roller surface noise."),
            ],
        ),
        (
            "3. CENTER VIEWPORT (LIVE FEED, CALIPERS & VIEW MODES)",
            "The primary operational display area rendering the slab, caliper overlays, and HUD data.",
            [
                ("Original View Tab", "Video Feed Toolbar: [ORIGINAL]", "Displays the unadulterated color video stream from the sensor with high-contrast caliper and edge overlays."),
                ("Grayscale View Tab", "Video Feed Toolbar: [GRAY]", "Displays the luminance intensity channel used for Sobel gradient differentiation."),
                ("Threshold View Tab", "Video Feed Toolbar: [THRESHOLD]", "Displays binary segmented black-and-white silhouette of the slab to verify edge isolation."),
                ("Detection View Tab", "Video Feed Toolbar: [DETECTION]", "Displays real-time Canny edge filter response highlighted in industrial cyan and green."),
                ("Thermal View Tab", "Video Feed Toolbar: [THERMAL]", "Renders false-color Inferno thermal heat map representing relative radiation intensity across the metal slab."),
                ("Measurement View Tab", "Video Feed Toolbar: [MEASUREMENT]", "Displays clean inspection stream with highlighted top and bottom edge tracking vector lines."),
                ("Toggle Edges Button", "Video Feed Toolbar: [EDGES]", "Shows or hides the laser-cyan edge detection boundary lines across the slab profile."),
                ("Freeze Stream Button", "Video Feed Toolbar: [FREEZE]", "Pauses video feed ingestion to inspect transient defects or take precision crosshair caliper measurements."),
                ("Fullscreen Button", "Video Feed Toolbar: [FULLSCREEN]", "Expands the viewport to full-screen display mode. Press F11 or ESC to return to windowed view."),
                ("Interactive Caliper Tooltip", "Video Canvas: Mouse Hover", "Hover mouse cursor anywhere across the slab to inspect instant localized X, Y, Top Edge, Bottom Edge, and Thickness values."),
            ],
        ),
        (
            "4. RIGHT PANEL (THICKNESS GAUGING, CALIBRATION & DVR)",
            "Displays quantitative measurement readouts, calibration wizards, and production reports.",
            [
                ("Big Digital Readout", "THICKNESS: Large Center Numerals", "Displays real-time calibrated slab thickness in millimeters (e.g., 174.2 mm) and uncalibrated pixel height (501.1 px)."),
                ("Statistical Summary", "THICKNESS: Minimum / Maximum / Average / Std Dev", "Live statistical distribution computed across all tracked horizontal cross-section columns across the ROI."),
                ("Detection Confidence Gauge", "THICKNESS: 'DETECTION CONFIDENCE' & 24-LED Bar", "Displays optical edge signal quality (0-100%). Colored green for solid boundaries, amber for fair, red for weak/low confidence."),
                ("Target & Tolerance Limits", "THICKNESS: 'TARGET', 'LOWER', 'UPPER' Inputs", "Operators can type mill thickness targets (e.g. 174.0 mm) and tolerance band boundaries (10.0 mm to 300.0 mm)."),
                ("Calibration Wizard", "CALIBRATION: [CALIBRATE] Button", "Click [CALIBRATE], then click Point 1 (slab top edge) and Point 2 (slab bottom edge) on the live video. Enter known distance in mm to calibrate."),
                ("Start / Stop Measurement", "OPERATION: [START MEASUREMENT] Button", "Toggles active mathematical thickness gauging on/off without interrupting the live video recording."),
                ("Capture Snapshot Button", "OPERATION: [CAPTURE IMAGE] Button", "Captures an instantaneous full-resolution PNG image of the live inspection display saved to data/captures/."),
                ("Generate Report Button", "OPERATION: [GENERATE REPORT] Button", "Exports a comprehensive quality audit CSV report containing timestamp, statistical metrics, and cross-section profile points to data/reports/."),
            ],
        ),
        (
            "5. BOTTOM BAR (CROSS-SECTION PROFILE & SYSTEM METRICS)",
            "Analytical cross-section curves, point-by-point data tables, and engine telemetry.",
            [
                ("Thickness Profile Chart", "Bottom Section: 'THICKNESS PROFILE' Tab", "Interactive continuous curve plotting mill thickness across the slab length. Features Target reference line, Tolerance limit lines, and interactive vertical cursor scrubber."),
                ("Measurement Points Table", "Bottom Section: 'MEASUREMENT POINTS' Tab", "Displays tabular discrete cross-section columns (#01 to #25) with exact X, Top Y, Bottom Y, pixel thickness, millimeter thickness, and NORMAL / OUT OF SPEC status."),
                ("SCADA Telemetry Strip", "Bottom Footer: Left Status Bar", "Displays live pipeline performance: input and processing FPS, frame processing latency in milliseconds, active resolution (1920x1080), Otsu threshold number, and calibration scale."),
                ("Active Source Label", "Bottom Footer: Right Status Bar", "Displays the active ingested file name, camera IP address, or local device identifier."),
            ],
        ),
    ]

    for title, subtitle, items in sections_data:
        story.append(KeepTogether([
            Paragraph(title, style_h1),
            Paragraph(subtitle, style_body),
            Spacer(1, 1.5 * mm),
        ]))

        table_rows = [
            [
                Paragraph("<b>FEATURE / OPERATION</b>", style_table_head),
                Paragraph("<b>UI LOCATION &amp; CONTROL</b>", style_table_head),
                Paragraph("<b>OPERATIONAL DESCRIPTION &amp; ACTION</b>", style_table_head),
            ]
        ]

        for feat, loc, desc in items:
            table_rows.append([
                Paragraph(feat, style_badge),
                Paragraph(loc, style_table_head),
                Paragraph(desc, style_table_cell),
            ])

        col_w = [115, 145, 260]
        t = Table(table_rows, colWidths=col_w, repeatRows=1)
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_bg_head),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, c_blue),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                ("BOX", (0, 0), (-1, -1), 0.8, c_border),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ])
        )

        story.append(t)
        story.append(Spacer(1, 5 * mm))

    def page_decorator(canvas, doc_ref):
        draw_page_watermark_and_chrome(canvas, doc_ref, logo_path)

    doc.build(story, onFirstPage=page_decorator, onLaterPages=page_decorator)
    return output_path


def open_pdf_manual(output_path: Path | None = None) -> Path:
    target_path = output_path or get_manual_pdf_path()
    if not target_path.exists():
        generate_features_manual_pdf(target_path)

    if sys.platform == "win32":
        try:
            os.startfile(str(target_path.resolve()))
        except Exception:
            import subprocess
            subprocess.Popen(["start", "", str(target_path.resolve())], shell=True)
    elif sys.platform == "darwin":
        import subprocess
        subprocess.Popen(["open", str(target_path.resolve())])
    else:
        import subprocess
        subprocess.Popen(["xdg-open", str(target_path.resolve())])

    return target_path
