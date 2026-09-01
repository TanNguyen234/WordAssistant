# Microsoft Word native backend

The native backend uses isolated worker processes so Office COM teardown faults cannot terminate the caller. Word runs invisibly with alerts disabled; documents and the application are closed on success and failure, and each initialized COM apartment is explicitly uninitialized.

Capability discovery advertises only operations included in the committed live-Word verification allowlist. Other callable paths remain experimental and are reported as unverified.

Native field refresh repaginates, updates main and linked story ranges, headers, footers, TOCs, and tables of figures, repaginates again, saves, and returns bounded cached-result evidence. Native PDF export uses `ExportAsFixedFormat` and never saves DOCX bytes to a PDF destination.

GitHub-hosted Windows runners provide a required native unit gate but do not
prove that Microsoft Word is installed. Live-Word evidence comes from the
committed integration tests executed on a Word-equipped machine; unavailable
Word environments must report a skip reason and may not claim native PASS.
