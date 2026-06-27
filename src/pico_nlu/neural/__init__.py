"""Neural components (BiLSTM-CRF slot filler, embeddings, trainer).

This subpackage is the ONLY place in pico-nlu that may import ``torch``. It degrades
gracefully when the ``[neural]`` extra is not installed: importing a neural submodule
without torch raises :class:`~pico_nlu.errors.ExtraNotInstalledError` with a helpful
install hint.

Implemented in PRD-06 (Neural Foundation) and PRD-07 (BiLSTM-CRF Slot Filler).
"""
