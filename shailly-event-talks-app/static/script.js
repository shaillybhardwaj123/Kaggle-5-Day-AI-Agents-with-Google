document.addEventListener("DOMContentLoaded", () => {
    // App State
    let releaseNotesData = [];
    let currentFilter = "all";
    let searchQuery = "";
    let selectedItemForTweet = null;

    // DOM Elements
    const feedContainer = document.getElementById("feed-container");
    const refreshBtn = document.getElementById("refresh-btn");
    const exportCsvBtn = document.getElementById("export-csv-btn");
    const spinner = document.getElementById("spinner");
    const lastUpdatedText = document.getElementById("last-updated-text");
    const searchInput = document.getElementById("search-input");
    const clearSearchBtn = document.getElementById("clear-search");
    const filterButtons = document.querySelectorAll(".filter-btn");
    
    // Theme Toggle Elements
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const sunIcon = document.getElementById("sun-icon");
    const moonIcon = document.getElementById("moon-icon");
    
    // State Views
    const loadingState = document.getElementById("loading-state");
    const errorState = document.getElementById("error-state");
    const emptyState = document.getElementById("empty-state");
    const retryBtn = document.getElementById("retry-btn");
    const resetFiltersBtn = document.getElementById("reset-filters-btn");
    
    // Modal Elements
    const tweetModal = document.getElementById("tweet-modal");
    const tweetTextarea = document.getElementById("tweet-textarea");
    const charCounter = document.getElementById("char-counter");
    const tweetLinkUrl = document.getElementById("tweet-link-url");
    const sendTweetBtn = document.getElementById("send-tweet-btn");
    const cancelTweetBtn = document.getElementById("cancel-tweet-btn");
    const closeModalBtn = document.getElementById("close-modal-btn");
    
    // Toast Element
    const toast = document.getElementById("toast");
    const toastMessage = document.getElementById("toast-message");

    // Theme Switcher Logic
    themeToggleBtn.addEventListener("click", () => {
        if (document.body.classList.contains("dark-theme")) {
            setTheme("light");
        } else {
            setTheme("dark");
        }
    });

    function setTheme(theme) {
        if (theme === "light") {
            document.body.classList.remove("dark-theme");
            document.body.classList.add("light-theme");
            sunIcon.classList.add("hidden");
            moonIcon.classList.remove("hidden");
            localStorage.setItem("theme", "light");
        } else {
            document.body.classList.remove("light-theme");
            document.body.classList.add("dark-theme");
            moonIcon.classList.add("hidden");
            sunIcon.classList.remove("hidden");
            localStorage.setItem("theme", "dark");
        }
    }

    const savedTheme = localStorage.getItem("theme") || "dark";
    setTheme(savedTheme);

    // Initialize Web App
    fetchReleaseNotes(false);

    // Event Listeners
    refreshBtn.addEventListener("click", () => fetchReleaseNotes(true));
    exportCsvBtn.addEventListener("click", exportToCSV);
    retryBtn.addEventListener("click", () => fetchReleaseNotes(true));
    resetFiltersBtn.addEventListener("click", resetFilters);
    
    // Search event handling
    searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        if (searchQuery.length > 0) {
            clearSearchBtn.style.display = "flex";
        } else {
            clearSearchBtn.style.display = "none";
        }
        renderFeed();
    });

    clearSearchBtn.addEventListener("click", () => {
        searchInput.value = "";
        searchQuery = "";
        clearSearchBtn.style.display = "none";
        renderFeed();
        searchInput.focus();
    });

    // Filter categories click handling
    filterButtons.forEach(button => {
        button.addEventListener("click", () => {
            filterButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");
            currentFilter = button.getAttribute("data-category");
            renderFeed();
        });
    });

    // Modal Events
    closeModalBtn.addEventListener("click", hideTweetModal);
    cancelTweetBtn.addEventListener("click", hideTweetModal);
    sendTweetBtn.addEventListener("click", triggerTwitterIntent);
    
    // Close modal if clicking outside the card
    tweetModal.addEventListener("click", (e) => {
        if (e.target === tweetModal) {
            hideTweetModal();
        }
    });

    // Global keydown Escape key event handler
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (!tweetModal.classList.contains("hidden")) {
                hideTweetModal();
            } else if (searchQuery.length > 0 || document.activeElement === searchInput) {
                searchInput.value = "";
                searchQuery = "";
                clearSearchBtn.style.display = "none";
                renderFeed();
                searchInput.blur();
            }
        }
    });

    // Textarea input character count tracking
    tweetTextarea.addEventListener("input", () => {
        const link = selectedItemForTweet ? selectedItemForTweet.entry.link : "";
        const length = getTwitterCharacterCount(tweetTextarea.value, link);
        const counterContainer = charCounter.parentElement;
        
        if (length > 280) {
            charCounter.textContent = `${280 - length} chars`;
            counterContainer.className = "char-counter-container limit-reached";
            sendTweetBtn.disabled = true;
        } else {
            charCounter.textContent = `${length} / 280`;
            if (length > 250) {
                counterContainer.className = "char-counter-container limit-warning";
            } else {
                counterContainer.className = "char-counter-container";
            }
            sendTweetBtn.disabled = false;
        }
    });

    // Fetch Release Notes API
    async function fetchReleaseNotes(forceRefresh = false) {
        setLoading(true);
        showState(null);
        
        try {
            const url = `/api/release-notes${forceRefresh ? '?refresh=true' : ''}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.status === "error") {
                throw new Error(result.message);
            }
            
            releaseNotesData = result.data;
            
            // Format last updated timestamp
            const updateTime = new Date(result.last_updated * 1000);
            lastUpdatedText.textContent = `Updated: ${updateTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
            
            if (result.status === "warning") {
                showToast(result.message, "error");
            } else if (forceRefresh) {
                showToast("Release notes refreshed successfully!", "success");
            }
            
            renderFeed();
        } catch (error) {
            console.error("Fetch failed:", error);
            document.getElementById("error-message").textContent = error.message || "Failed to parse XML feed from Google Cloud.";
            showState("error");
            lastUpdatedText.textContent = "Update failed";
        } finally {
            setLoading(false);
        }
    }

    // Set Loading States
    function setLoading(isLoading) {
        if (isLoading) {
            refreshBtn.classList.add("loading");
            refreshBtn.disabled = true;
            document.querySelector(".status-dot").className = "status-dot loading";
            if (releaseNotesData.length === 0) {
                showState("loading");
            }
        } else {
            refreshBtn.classList.remove("loading");
            refreshBtn.disabled = false;
            document.querySelector(".status-dot").className = "status-dot green";
        }
    }

    // Reset Filters helper
    function resetFilters() {
        searchInput.value = "";
        searchQuery = "";
        clearSearchBtn.style.display = "none";
        currentFilter = "all";
        
        filterButtons.forEach(btn => {
            if (btn.getAttribute("data-category") === "all") {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
        
        renderFeed();
    }

    // Export to CSV function
    function exportToCSV() {
        if (!releaseNotesData || releaseNotesData.length === 0) {
            showToast("No data available to export.", "error");
            return;
        }

        const exportedRows = [];
        // CSV Header
        exportedRows.push(["Date", "Update Type", "Description", "Link"].map(quoteValue).join(","));

        releaseNotesData.forEach(entry => {
            entry.items.forEach(item => {
                // Check if item matches current filter/search
                const itemTypeLower = item.type.toLowerCase();
                let categoryMatches = false;
                
                if (currentFilter === "all") {
                    categoryMatches = true;
                } else if (currentFilter === "issue") {
                    categoryMatches = itemTypeLower.includes("issue") || itemTypeLower.includes("bug");
                } else if (currentFilter === "change") {
                    categoryMatches = itemTypeLower.includes("change");
                } else if (currentFilter === "breaking") {
                    categoryMatches = itemTypeLower.includes("breaking") || itemTypeLower.includes("deprecation");
                } else {
                    categoryMatches = itemTypeLower.includes(currentFilter);
                }

                if (!categoryMatches) return;

                if (searchQuery.length > 0) {
                    const matchesSearchText = item.text_content.toLowerCase().includes(searchQuery);
                    const matchesType = item.type.toLowerCase().includes(searchQuery);
                    const matchesDate = entry.date.toLowerCase().includes(searchQuery);
                    if (!(matchesSearchText || matchesType || matchesDate)) return;
                }

                const row = [
                    entry.date,
                    item.type,
                    item.text_content,
                    entry.link
                ];
                exportedRows.push(row.map(quoteValue).join(","));
            });
        });

        if (exportedRows.length <= 1) {
            showToast("No filtered updates to export.", "error");
            return;
        }

        function quoteValue(val) {
            if (val === null || val === undefined) return '""';
            const strVal = String(val);
            const escaped = strVal.replace(/"/g, '""');
            return `"${escaped}"`;
        }

        const csvContent = "\uFEFF" + exportedRows.join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement("a");
        link.setAttribute("href", url);
        const filterName = currentFilter.toUpperCase();
        const timestamp = new Date().toISOString().slice(0, 10);
        link.setAttribute("download", `bigquery_release_notes_${filterName}_${timestamp}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast(`Exported ${exportedRows.length - 1} rows to CSV!`, "success");
    }

    // Render Feed based on active filters and search queries
    function renderFeed() {
        feedContainer.innerHTML = "";
        
        if (!releaseNotesData || releaseNotesData.length === 0) {
            showState("empty");
            return;
        }

        let totalRenderedItems = 0;

        releaseNotesData.forEach(entry => {
            // Filter items in this entry
            const filteredItems = entry.items.filter(item => {
                // 1. Filter by category
                const itemTypeLower = item.type.toLowerCase();
                let categoryMatches = false;
                
                if (currentFilter === "all") {
                    categoryMatches = true;
                } else if (currentFilter === "issue") {
                    categoryMatches = itemTypeLower.includes("issue") || itemTypeLower.includes("bug");
                } else if (currentFilter === "change") {
                    categoryMatches = itemTypeLower.includes("change");
                } else if (currentFilter === "breaking") {
                    categoryMatches = itemTypeLower.includes("breaking") || itemTypeLower.includes("deprecation");
                } else {
                    categoryMatches = itemTypeLower.includes(currentFilter);
                }

                if (!categoryMatches) return false;

                // 2. Filter by search query
                if (searchQuery.length > 0) {
                    const matchesSearchText = item.text_content.toLowerCase().includes(searchQuery);
                    const matchesType = item.type.toLowerCase().includes(searchQuery);
                    const matchesDate = entry.date.toLowerCase().includes(searchQuery);
                    return matchesSearchText || matchesType || matchesDate;
                }

                return true;
            });

            // If we have items remaining, render the group
            if (filteredItems.length > 0) {
                const dateGroup = document.createElement("div");
                dateGroup.className = "date-group";
                
                // Sidebar date marker
                const sidebar = document.createElement("div");
                sidebar.className = "date-sidebar";
                
                const dateBadge = document.createElement("div");
                dateBadge.className = "date-badge";
                dateBadge.textContent = entry.date;
                
                const relativeTime = document.createElement("div");
                relativeTime.className = "date-relative";
                relativeTime.textContent = getRelativeTimeString(entry.updated);
                
                sidebar.appendChild(dateBadge);
                sidebar.appendChild(relativeTime);
                dateGroup.appendChild(sidebar);
                
                // Card list for this date
                const listContainer = document.createElement("div");
                listContainer.className = "date-updates-list";
                
                filteredItems.forEach(item => {
                    const card = createUpdateCard(item, entry);
                    listContainer.appendChild(card);
                    totalRenderedItems++;
                });
                
                dateGroup.appendChild(listContainer);
                feedContainer.appendChild(dateGroup);
            }
        });

        // Toggle views based on final count
        if (totalRenderedItems === 0) {
            showState("empty");
        } else {
            showState(null);
        }
    }

    // Create a Card Element
    function createUpdateCard(item, entry) {
        const card = document.createElement("div");
        const typeLower = item.type.toLowerCase();
        
        // Determine category class for styling
        let categoryClass = "category-update";
        if (typeLower.includes("feature")) categoryClass = "category-feature";
        else if (typeLower.includes("announcement")) categoryClass = "category-announcement";
        else if (typeLower.includes("issue") || typeLower.includes("bug")) categoryClass = "category-issue";
        else if (typeLower.includes("change")) categoryClass = "category-change";
        else if (typeLower.includes("breaking") || typeLower.includes("deprecation")) categoryClass = "category-breaking";
        
        card.className = `update-card ${categoryClass}`;
        
        // Card Header
        const header = document.createElement("div");
        header.className = "card-header";
        
        const badgeWrapper = document.createElement("div");
        badgeWrapper.className = "badge-wrapper";
        
        const badge = document.createElement("span");
        let badgeType = "update";
        if (typeLower.includes("feature")) badgeType = "feature";
        else if (typeLower.includes("announcement")) badgeType = "announcement";
        else if (typeLower.includes("issue") || typeLower.includes("bug")) badgeType = "issue";
        else if (typeLower.includes("change")) badgeType = "change";
        else if (typeLower.includes("breaking") || typeLower.includes("deprecation")) badgeType = "breaking";
        
        badge.className = `category-badge ${badgeType}`;
        badge.textContent = item.type;
        badgeWrapper.appendChild(badge);
        header.appendChild(badgeWrapper);
        
        // Actions (Share & Original link)
        const actions = document.createElement("div");
        actions.className = "card-actions";
        
        // Tweet Button
        const tweetBtn = document.createElement("button");
        tweetBtn.className = "action-icon-btn tweet-btn";
        tweetBtn.title = "Tweet this update";
        tweetBtn.setAttribute("aria-label", "Tweet this update");
        tweetBtn.innerHTML = `
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
        `;
        tweetBtn.addEventListener("click", () => showTweetModal(item, entry));
        actions.appendChild(tweetBtn);

        // Copy Button
        const copyBtn = document.createElement("button");
        copyBtn.className = "action-icon-btn copy-btn";
        copyBtn.title = "Copy to clipboard";
        copyBtn.setAttribute("aria-label", "Copy update description to clipboard");
        copyBtn.innerHTML = `
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        `;
        copyBtn.addEventListener("click", () => {
            const copyText = `BigQuery ${item.type} (${entry.date}):\n${item.text_content}\n\nLink: ${entry.link}`;
            navigator.clipboard.writeText(copyText).then(() => {
                showToast("Copied update to clipboard!", "success");
                
                // Visual feedback checkmark swap
                const originalSVG = copyBtn.innerHTML;
                copyBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                `;
                copyBtn.classList.add("copied");
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalSVG;
                    copyBtn.classList.remove("copied");
                }, 1500);
            }).catch(err => {
                console.error("Clipboard copy failed:", err);
                showToast("Failed to copy text.", "error");
            });
        });
        actions.appendChild(copyBtn);
        
        // Link Button
        if (entry.link) {
            const linkBtn = document.createElement("a");
            linkBtn.className = "action-icon-btn link-btn";
            linkBtn.href = entry.link;
            linkBtn.target = "_blank";
            linkBtn.rel = "noopener noreferrer";
            linkBtn.title = "View in Google Docs";
            linkBtn.setAttribute("aria-label", "View original release note page");
            linkBtn.innerHTML = `
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
            `;
            actions.appendChild(linkBtn);
        }
        
        header.appendChild(actions);
        card.appendChild(header);
        
        // Card Body with highlights
        const body = document.createElement("div");
        body.className = "card-body";
        body.innerHTML = highlightSearchText(item.content, searchQuery);
        card.appendChild(body);
        
        return card;
    }

    // Safely highlights text nodes in HTML content matching query
    function highlightSearchText(htmlContent, query) {
        if (!query || query.trim().length === 0) return htmlContent;
        
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = htmlContent;
        
        const escQuery = query.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const regex = new RegExp(`(${escQuery})`, 'gi');
        
        function highlightNode(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent;
                if (regex.test(text)) {
                    const span = document.createElement("span");
                    span.innerHTML = text.replace(regex, `<mark class="search-highlight">$1</mark>`);
                    node.parentNode.replaceChild(span, node);
                }
            } else if (node.nodeType === Node.ELEMENT_NODE && node.nodeName !== "A" && node.nodeName !== "CODE" && node.nodeName !== "SCRIPT" && node.nodeName !== "STYLE") {
                Array.from(node.childNodes).forEach(highlightNode);
            }
        }
        
        Array.from(tempDiv.childNodes).forEach(highlightNode);
        return tempDiv.innerHTML;
    }

    // Toggle different app screens
    function showState(state) {
        // Hide all states first
        loadingState.classList.add("hidden");
        errorState.classList.add("hidden");
        emptyState.classList.add("hidden");
        feedContainer.classList.remove("hidden");
        
        if (state === "loading") {
            loadingState.classList.remove("hidden");
            feedContainer.classList.add("hidden");
        } else if (state === "error") {
            errorState.classList.remove("hidden");
            feedContainer.classList.add("hidden");
        } else if (state === "empty") {
            emptyState.classList.remove("hidden");
        }
    }

    // Show Tweet Composition Modal
    function showTweetModal(item, entry) {
        selectedItemForTweet = { item, entry };
        
        // Base tweet construction matching 280 char limit
        const titleText = `BigQuery ${item.type} (${entry.date}): `;
        const hashtags = `\n\n#BigQuery #GoogleCloud`;
        const link = entry.link;
        
        // Render links in preview area
        tweetLinkUrl.textContent = link;
        
        // Deduct spaces and link characters for Twitter link processing
        // Note: Twitter processes links as 23 characters using its t.co shortener.
        const TWITTER_LINK_LEN = 23;
        const availableLength = 280 - titleText.length - hashtags.length - TWITTER_LINK_LEN - 5; // buffer
        
        let cleanedSummary = item.text_content;
        // Clean double spaces or excess breaks
        cleanedSummary = cleanedSummary.replace(/\s+/g, " ");
        
        // Truncate summary if too long
        if (cleanedSummary.length > availableLength) {
            cleanedSummary = cleanedSummary.substring(0, availableLength).trim() + "...";
        }
        
        const initialText = `${titleText}${cleanedSummary}${hashtags}`;
        tweetTextarea.value = initialText;
        
        // Update character counter:
        // Use standard length but compensate for Twitter's 23 char link mapping
        const currentLength = getTwitterCharacterCount(initialText, link);
        const counterContainer = charCounter.parentElement;
        
        if (currentLength > 280) {
            charCounter.textContent = `${280 - currentLength} chars`;
            counterContainer.className = "char-counter-container limit-reached";
            sendTweetBtn.disabled = true;
        } else {
            charCounter.textContent = `${currentLength} / 280`;
            if (currentLength > 250) {
                counterContainer.className = "char-counter-container limit-warning";
            } else {
                counterContainer.className = "char-counter-container";
            }
            sendTweetBtn.disabled = false;
        }
        
        // Display modal
        tweetModal.classList.remove("hidden");
        tweetTextarea.focus();
        // Place cursor at the end
        tweetTextarea.setSelectionRange(tweetTextarea.value.length, tweetTextarea.value.length);
    }

    function hideTweetModal() {
        tweetModal.classList.add("hidden");
        selectedItemForTweet = null;
    }

    // Calculate Twitter characters correctly (links are mapped to 23 chars)
    function getTwitterCharacterCount(text, link) {
        let count = text.length;
        if (link && text.includes(link)) {
            // Replace link with 23 char equivalent in calculation
            count = text.replace(link, "X".repeat(23)).length;
        }
        return count;
    }

    // Opens a new window with X Web Intent
    function triggerTwitterIntent() {
        if (!selectedItemForTweet) return;
        
        const tweetText = tweetTextarea.value;
        const link = selectedItemForTweet.entry.link;
        
        // Twitter Intent URL
        let url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;
        if (link && !tweetText.includes(link)) {
            url += `&url=${encodeURIComponent(link)}`;
        }
        
        window.open(url, "_blank", "noopener,noreferrer");
        hideTweetModal();
        showToast("Twitter sharing page opened!", "success");
    }

    // Relative Time Helper
    function getRelativeTimeString(dateString) {
        if (!dateString) return "";
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now - date;
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) {
                // Check hours
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                if (diffHours === 0) {
                    const diffMins = Math.floor(diffMs / (1000 * 60));
                    return diffMins <= 1 ? "Just now" : `${diffMins}m ago`;
                }
                return `${diffHours}h ago`;
            } else if (diffDays === 1) {
                return "Yesterday";
            } else if (diffDays < 7) {
                return `${diffDays} days ago`;
            } else if (diffDays < 30) {
                const weeks = Math.floor(diffDays / 7);
                return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
            } else {
                const months = Math.floor(diffDays / 30);
                return `${months} month${months > 1 ? 's' : ''} ago`;
            }
        } catch (e) {
            return "";
        }
    }

    // Show Notification Toast
    function showToast(message, type = "success") {
        toastMessage.textContent = message;
        toast.className = `toast ${type}`;
        
        // Show
        toast.classList.remove("hidden");
        
        // Clear previous timeout if any
        if (window.toastTimeout) {
            clearTimeout(window.toastTimeout);
        }
        
        // Hide after 3.5 seconds
        window.toastTimeout = setTimeout(() => {
            toast.classList.add("hidden");
        }, 3500);
    }
});
