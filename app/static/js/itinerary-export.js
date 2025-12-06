/**
 * Itinerary Export Functionality
 * Handles download (PDF/print), share, and copy link features
 */

document.addEventListener('DOMContentLoaded', function() {
  // DOM Elements
  const downloadBtn = document.getElementById('downloadItineraryBtn');
  const shareBtn = document.getElementById('shareItineraryBtn');
  const shareModal = document.getElementById('shareModal');
  const closeShareModalBtn = document.getElementById('closeShareModal');
  const copyLinkBtn = document.getElementById('copyLinkBtn');
  const shareLinkInput = document.getElementById('shareLink');
  const printItineraryBtn = document.getElementById('printItineraryBtn');

  // Download button - triggers print dialog for PDF
  if (downloadBtn) {
    downloadBtn.addEventListener('click', function() {
      triggerPrint();
    });
  }

  // Share button - opens share modal
  if (shareBtn) {
    shareBtn.addEventListener('click', function() {
      openShareModal();
    });
  }

  // Close modal button
  if (closeShareModalBtn) {
    closeShareModalBtn.addEventListener('click', function() {
      closeShareModal();
    });
  }

  // Close modal when clicking outside
  if (shareModal) {
    shareModal.addEventListener('click', function(e) {
      if (e.target === shareModal) {
        closeShareModal();
      }
    });
  }

  // Copy link button
  if (copyLinkBtn && shareLinkInput) {
    copyLinkBtn.addEventListener('click', function() {
      copyToClipboard();
    });
  }

  // Print button inside modal
  if (printItineraryBtn) {
    printItineraryBtn.addEventListener('click', function() {
      closeShareModal();
      setTimeout(triggerPrint, 300);
    });
  }

  // Close modal on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && shareModal && shareModal.classList.contains('show')) {
      closeShareModal();
    }
  });

  /**
   * Open share modal
   */
  function openShareModal() {
    if (shareModal) {
      shareModal.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  }

  /**
   * Close share modal
   */
  function closeShareModal() {
    if (shareModal) {
      shareModal.classList.remove('show');
      document.body.style.overflow = '';
    }
  }

  /**
   * Copy share link to clipboard
   */
  function copyToClipboard() {
    if (!shareLinkInput) return;

    // Select the text
    shareLinkInput.select();
    shareLinkInput.setSelectionRange(0, 99999); // For mobile

    // Try using the Clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareLinkInput.value)
        .then(() => {
          showCopyFeedback(true);
        })
        .catch(() => {
          // Fallback to execCommand
          document.execCommand('copy');
          showCopyFeedback(true);
        });
    } else {
      // Fallback for older browsers
      document.execCommand('copy');
      showCopyFeedback(true);
    }
  }

  /**
   * Show copy feedback
   */
  function showCopyFeedback(success) {
    if (!copyLinkBtn) return;

    const originalText = copyLinkBtn.innerHTML;
    
    if (success) {
      copyLinkBtn.innerHTML = '✓ Copied!';
      copyLinkBtn.classList.add('copied');
    } else {
      copyLinkBtn.innerHTML = '✗ Failed';
    }

    setTimeout(() => {
      copyLinkBtn.innerHTML = originalText;
      copyLinkBtn.classList.remove('copied');
    }, 2000);
  }

  /**
   * Trigger print dialog for PDF download
   */
  function triggerPrint() {
    window.print();
  }
});

