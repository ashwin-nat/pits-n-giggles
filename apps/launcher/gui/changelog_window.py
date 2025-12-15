# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import re
import webbrowser
from datetime import datetime
from typing import Any, Dict, List

import markdown
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt, QTimer, QUrl
from PySide6.QtGui import QFont, QIcon, QImage, QPixmap, QTextDocument
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QTextBrowser, QVBoxLayout)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ImageLoadingTextBrowser(QTextBrowser):
    """QTextBrowser subclass that loads external images asynchronously"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager(self)
        self.pending_images = {}  # url -> reply mapping
        self.loaded_images = []  # Queue of loaded images

        # Timer to batch image updates
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._batch_update)
        self.update_timer.setInterval(100)  # Wait 100ms after last image

    def loadResource(self, resource_type: int, url: QUrl) -> Any:
        """Override to load external images asynchronously"""
        if (resource_type == QTextDocument.ResourceType.ImageResource) and (url.scheme() in {'http', 'https'}):
            url_string = url.toString()

            # Check if we already have this image cached
            if cached := super().loadResource(resource_type, url):
                return cached

            # Start async request if not already pending
            if url_string not in self.pending_images:
                request = QNetworkRequest(url)
                reply = self.network_manager.get(request)
                reply.finished.connect(lambda: self._on_image_loaded(url, reply))
                self.pending_images[url_string] = reply

            # Return empty data for now - will update when loaded
            return b''

        return super().loadResource(resource_type, url)

    def _on_image_loaded(self, url: QUrl, reply: QNetworkReply):
        """Handle completed image download"""
        url_string = url.toString()

        if url_string in self.pending_images:
            del self.pending_images[url_string]

        if reply.error() == reply.NetworkError.NoError:
            image_data = reply.readAll()

            # Resize large images to improve performance
            image = QImage.fromData(image_data)
            if not image.isNull():
                # Max width for images (adjust as needed)
                max_width = 800
                if image.width() > max_width:
                    # Scale down large images
                    image = image.scaledToWidth(
                        max_width,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    # Convert back to bytes
                    pixmap = QPixmap.fromImage(image)
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    pixmap.save(buffer, "PNG")
                    image_data = byte_array

            # Add the image to the document's resources
            self.document().addResource(
                QTextDocument.ResourceType.ImageResource,
                url,
                image_data
            )

            # Queue this image for batch update
            self.loaded_images.append(url_string)

            # Restart the timer (batches updates if multiple images load quickly)
            self.update_timer.start()

        reply.deleteLater()

    def _batch_update(self):
        """Batch update all loaded images at once"""
        if self.loaded_images:
            # Only reflow once for all loaded images
            current_html = self.toHtml()
            self.setHtml(current_html)
            self.loaded_images.clear()

class ChangelogWindow(QDialog):
    """Window to display version changelogs"""

    _WIDTH_REGEX = re.compile(r'<img\s+([^>]*?)\s*width="[^"]*"([^>]*?)>')
    _HEIGHT_REGEX = re.compile(r'<img\s+([^>]*?)\s*height="[^"]*"([^>]*?)>')

    def __init__(self, parent, newer_versions: List[Dict], icons: Dict[str, QIcon]):
        super().__init__(parent)
        self.newer_versions = newer_versions
        self.icons = icons
        self.setup_ui()

    def setup_ui(self):
        """Setup the changelog window UI"""
        self.setWindowTitle("What's New")
        self.setMinimumSize(800, 600)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
            }
            QLabel {
                color: #d4d4d4;
                background-color: transparent;
            }
            QTextBrowser {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 16px;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: 1px solid #1177bb;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e3e;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4e4e4e;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        # Icon and title
        if self.icons.get("updates"):
            icon_label = QLabel()
            icon_label.setPixmap(self.icons["updates"].pixmap(32, 32))
            icon_label.setFixedSize(32, 32)
            header_layout.addWidget(icon_label)

        title_label = QLabel("New Updates Available")
        title_label.setFont(QFont("Formula1", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Info text
        if len(self.newer_versions) == 1:
            info_text = "There is 1 new version available:"
        else:
            info_text = f"There are {len(self.newer_versions)} new versions available:"

        info_label = QLabel(info_text)
        info_label.setFont(QFont("Roboto", 10))
        info_label.setStyleSheet("color: #cccccc;")
        main_layout.addWidget(info_label)

        # Single text browser for all changelogs with image loading support
        self.changelog_browser = ImageLoadingTextBrowser()
        self.changelog_browser.setOpenExternalLinks(True)

        # Combine all changelogs into one HTML document
        combined_html = self._create_combined_changelog()
        self.changelog_browser.setHtml(combined_html)

        main_layout.addWidget(self.changelog_browser)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Download button
        download_btn = QPushButton("Download Updates")
        download_btn.setMinimumWidth(140)
        if self.icons.get("download"):
            download_btn.setIcon(self.icons["download"])
        download_btn.clicked.connect(self._on_download_clicked)
        button_layout.addWidget(download_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _create_combined_changelog(self) -> str:
        """Create a single HTML document with all changelogs"""
        markdown_parts = []

        for version_info in self.newer_versions:
            version_name = version_info.get("name", "Unknown Version")
            published_at = version_info.get("published_at", "")
            body = version_info.get("body", "No changelog available.")
            release_url = version_info.get("html_url", "")

            # Format the header
            header = f"# {version_name}"

            # Add date if available
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    date_str = dt.strftime("%B %d, %Y")
                    header += f" - *{date_str}*"
                except ValueError:
                    pass

            markdown_parts.append(header)
            markdown_parts.append(body)

            # Add release URL at the bottom
            if release_url:
                markdown_parts.append(f"\n**Release URL:** [{release_url}]({release_url})")

            markdown_parts.append("---")  # Horizontal rule separator

        # Join all parts with double newlines
        combined_markdown = "\n\n".join(markdown_parts)

        # Convert to HTML with styling
        return self._markdown_to_html(combined_markdown)

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown text to HTML with custom styling"""
        # Convert markdown to HTML
        html = markdown.markdown(
            markdown_text,
            extensions=['fenced_code', 'tables', 'nl2br']
        )

        # Remove width and height attributes from img tags to preserve aspect ratio
        html = self._WIDTH_REGEX.sub(r'<img \1\2>', html)
        html = self._HEIGHT_REGEX.sub(r'<img \1\2>', html)

        # Wrap in styled div
        styled_html = f"""
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 11px;
                line-height: 1.6;
                color: #d4d4d4;
            }}
            h1 {{
                color: #4ec9b0;
                font-size: 18px;
                margin-top: 24px;
                margin-bottom: 12px;
                border-bottom: 2px solid #3e3e3e;
                padding-bottom: 8px;
            }}
            h1:first-child {{
                margin-top: 0;
            }}
            h2 {{
                color: #569cd6;
                font-size: 16px;
                margin-top: 20px;
                margin-bottom: 8px;
            }}
            h3 {{
                color: #569cd6;
                font-size: 14px;
                margin-top: 16px;
                margin-bottom: 8px;
            }}
            h4, h5, h6 {{
                color: #569cd6;
                margin-top: 12px;
                margin-bottom: 6px;
            }}
            code {{
                background-color: #1e1e1e;
                color: #ce9178;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            pre {{
                background-color: #1e1e1e;
                padding: 12px;
                border-radius: 4px;
                border: 1px solid #3e3e3e;
                overflow-x: auto;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            a {{
                color: #4ec9b0;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            ul, ol {{
                margin-left: 20px;
                margin-bottom: 12px;
            }}
            li {{
                margin-bottom: 4px;
            }}
            blockquote {{
                border-left: 3px solid #4ec9b0;
                padding-left: 12px;
                margin-left: 0;
                color: #cccccc;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 12px 0;
            }}
            th, td {{
                border: 1px solid #3e3e3e;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #1e1e1e;
                font-weight: bold;
            }}
            hr {{
                border: none;
                border-top: 1px solid #3e3e3e;
                margin: 32px 0;
            }}
            em {{
                color: #808080;
                font-style: italic;
            }}
            img {{
                max-width: 100%;
                height: auto !important;
                display: block;
                margin: 16px auto;
                border-radius: 4px;
                border: 1px solid #3e3e3e;
            }}
        </style>
        {html}
        """

        return styled_html

    def _on_download_clicked(self):
        """Open the downloads page in browser"""
        webbrowser.open("https://pitsngiggles.com/releases")
