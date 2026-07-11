        const recognitionStatus = document.getElementById('recognition-status');
        const toggleKinectButton = document.getElementById('toggle-kinect-button');
        const attendanceButton = document.getElementById('attendance-button');
        const profileMenu = document.querySelector('.profile-menu');
        const profileMenuButton = document.getElementById('profile-menu-button');
        const profileMark = profileMenuButton ? profileMenuButton.querySelector('.brand-mark') : null;
        const profilePanel = document.getElementById('profile-panel');
        const profileAlertAnchor = document.getElementById('profile-alert-anchor');
        const alertBellButton = document.getElementById('alert-bell-button');
        const alertPanel = document.getElementById('alert-panel');
        const colorImage = document.getElementById('kinect-color-image');
        const depthImage = document.getElementById('kinect-depth-image');
        const studentTrackList = document.getElementById('student-track-list');
        const coursePickerShell = document.getElementById('course-picker-shell');
        const courseSelect = document.getElementById('course-select');
        const courseCurrentLine = document.getElementById('course-current-line');
        const personCountPill = document.getElementById('person-count-pill');
        const statusFeedMessage = document.getElementById('status-feed-message');
        const dashboardNav = document.querySelector('.nav-item[href="#kinect-streams"]');
        const studentSidebarList = document.getElementById('student-sidebar-list');
        const recognitionSection = document.getElementById('recognized-students');
        const studentDetailSection = document.getElementById('student-detail');
        const studentDetailName = document.getElementById('student-detail-name');
        const studentDetailSubtitle = document.getElementById('student-detail-subtitle');
        const studentDetailBackButton = document.getElementById('student-detail-back');
        const studentExportCsvButton = document.getElementById('student-export-csv-button');
        const studentSummaryName = document.getElementById('student-summary-name');
        const studentSummaryStudentId = document.getElementById('student-summary-student-id');
        const studentSummaryCollege = document.getElementById('student-summary-college');
        const studentSummaryDepartment = document.getElementById('student-summary-department');
        const studentSummaryStatus = document.getElementById('student-summary-status');
        const studentSummaryDuration = document.getElementById('student-summary-duration');
        const studentDetailPresenceChart = document.getElementById('student-detail-presence-chart');
        const studentMetricCharts = document.querySelectorAll('.mock-metric-chart');
        const MOCK_METRIC_CSV_BASE = window.__URLS__.mockMetrics;
        const mockMetricCache = new Map();
        const liveMetricState = new Map();
        const METRIC_HISTORY_SECONDS = 300;
        const METRIC_BUCKET_COUNT = 5;
        const METRIC_LINE_DISPLAY_POINTS = 4;
        const LIVE_CLASSROOM_METRIC_KEYS = new Set([
            'focus-ratio',
            'head-stability',
            'fatigue',
            'posture-angle',
            'desk-distance',
            'stillness',
            'hand-raise',
            'shared-attention',
        ]);
        const PERSONAL_EXPORT_HISTORY_METRIC_KEYS = [
            'assignment-score',
            'attendance-rate',
        ];
        const METRIC_HISTORY_KEYS = new Set([
            ...LIVE_CLASSROOM_METRIC_KEYS,
            ...PERSONAL_EXPORT_HISTORY_METRIC_KEYS,
        ]);
        const enrollModal = document.getElementById('enroll-modal');
        const enrollForm = document.getElementById('enroll-form');
        const enrollTempId = document.getElementById('enroll-temp-id');
        const enrollName = document.getElementById('enroll-name');
        const enrollStudentId = document.getElementById('enroll-student-id');
        const enrollCollege = document.getElementById('enroll-college');
        const enrollDepartment = document.getElementById('enroll-department');
        const enrollStatus = document.getElementById('enroll-status');
        const enrollSubmitButton = document.getElementById('enroll-submit-button');
        const enrollPreviewImage = document.getElementById('enroll-preview-image');
        const captureFrameButton = document.getElementById('capture-frame-button');
        const captureCounter = document.getElementById('capture-counter');
        const captureSlots = Array.from(document.querySelectorAll('#capture-slots .capture-slot'));
        const enrollCloseButton = document.getElementById('enroll-close-button');
        const enrollCancelButton = document.getElementById('enroll-cancel-button');
        const teacherChatWidget = document.getElementById('teacher-chat-widget');
        const teacherChatPanel = document.getElementById('teacher-chat-panel');
        const teacherChatToggle = document.getElementById('teacher-chat-toggle');
        const teacherChatClose = document.getElementById('teacher-chat-close');
        const teacherChatBody = document.getElementById('teacher-chat-body');
        const teacherChatInput = document.getElementById('teacher-chat-input');
        const teacherChatSend = document.getElementById('teacher-chat-send');
        const themeToggleButton = document.getElementById('theme-toggle-button');
        const rawManagerCourses = window.__DATA__.managerCourses;
        const managerCourseItems = Array.isArray(rawManagerCourses)
            ? rawManagerCourses
            : (rawManagerCourses && typeof rawManagerCourses === 'object' ? Object.values(rawManagerCourses) : []);
        const managerCourses = Array.isArray(managerCourseItems)
            ? managerCourseItems
                .map((item) => ({
                    id: typeof item === 'string'
                        ? String(item).trim()
                        : String(item?.id ?? item?.course_id ?? item?.course ?? item?.value ?? item?.name ?? item?.title ?? item?.label ?? '').trim(),
                    name: typeof item === 'string'
                        ? String(item).trim()
                        : String(item?.name ?? item?.course_name ?? item?.title ?? item?.label ?? item?.id ?? item?.course_id ?? '').trim(),
                }))
                .filter((item) => item.id && item.name)
            : [];
        const defaultCourseId = window.__DATA__.defaultCourseId;
        const defaultCourseName = window.__DATA__.defaultCourseName;
        if (!managerCourses.length && (defaultCourseId || defaultCourseName)) {
            managerCourses.push({
                id: String(defaultCourseId || defaultCourseName || '').trim(),
                name: String(defaultCourseName || defaultCourseId || '').trim(),
            });
        }
        const currentUserAccount = window.__DATA__.userAccount;
        let lastKinectStatus = null;
        let attendanceMode = false;
        let trainingRegistry = new Map();
        let currentEnrollCaptureCount = 0;
        let currentView = 'dashboard';
        let selectedStudentId = '';
        let currentMetricStudentKey = '';
        let metricSimulationTimer = null;
        let profileMenuCloseTimer = null;
        let isKinectToggling = false;
        let isAttendanceToggling = false;
        let selectedCourseId = '';
        let selectedCourseName = '';
        let lastSyncedCourseKey = '';
        const initialTrainingStudents = window.__DATA__.trainingStudents;
        const PROFILE_MENU_CLOSE_DELAY_MS = 220;
        const COURSE_STORAGE_KEY = `attendance_course_${currentUserAccount || 'default'}`;
        const THEME_STORAGE_KEY = 'dashboard_theme_preference';

        function normalizeDashboardTheme(themeName) {
            return themeName === 'dark' ? 'dark' : 'light';
        }

        function setDashboardTheme(themeName, persist = true) {
            const nextTheme = normalizeDashboardTheme(themeName);
            document.documentElement.setAttribute('data-dashboard-theme', nextTheme);

            if (themeToggleButton) {
                const toggleToDark = nextTheme !== 'dark';
                themeToggleButton.textContent = toggleToDark ? '切換為深色版' : '切換為淺色版';
                themeToggleButton.setAttribute('aria-pressed', nextTheme === 'dark' ? 'true' : 'false');
                themeToggleButton.dataset.currentTheme = nextTheme;
            }

            if (persist) {
                try {
                    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
                } catch (error) {
                    console.warn('Unable to persist dashboard theme.', error);
                }
            }
        }

        function initializeDashboardTheme() {
            let initialTheme = normalizeDashboardTheme(document.documentElement.getAttribute('data-dashboard-theme') || 'light');
            try {
                const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
                initialTheme = normalizeDashboardTheme(savedTheme || initialTheme);
            } catch (error) {
                console.warn('Unable to read saved dashboard theme.', error);
            }
            setDashboardTheme(initialTheme, false);
        }

        function setRecognitionMessage(message) {
            recognitionStatus.textContent = message || '';
        }

        function getCourseById(courseId) {
            const target = String(courseId || '').trim();
            return managerCourses.find((item) => String(item.id || '').trim() === target) || null;
        }

        function buildCourseSyncKey(courseId, courseName) {
            const normalizedId = String(courseId || '').trim();
            const normalizedName = String(courseName || '').trim();
            return `${normalizedId}::${normalizedName}`;
        }

        async function syncSelectedCourseToServer() {
            const nextId = String(selectedCourseId || '').trim();
            const nextName = String(selectedCourseName || '').trim();
            const nextKey = buildCourseSyncKey(nextId, nextName);
            if (!nextName || nextKey === lastSyncedCourseKey) {
                return;
            }

            try {
                const response = await fetch(window.__URLS__.updateAttendanceCourse, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        course_id: nextId,
                        course_name: nextName,
                    }),
                });
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.message || '課程同步失敗。');
                }

                if (payload.current_course) {
                    lastSyncedCourseKey = buildCourseSyncKey(
                        payload.current_course.course_id || '',
                        payload.current_course.course_name || '',
                    );
                } else {
                    lastSyncedCourseKey = nextKey;
                }

                const latestSelectionKey = buildCourseSyncKey(selectedCourseId, selectedCourseName);
                if (latestSelectionKey && latestSelectionKey !== lastSyncedCourseKey) {
                    window.setTimeout(() => {
                        syncSelectedCourseToServer();
                    }, 0);
                }
            } catch (error) {
                console.warn('Unable to sync selected course.', error);
            }
        }

        function setSelectedCourse(courseId, courseName, persist = true) {
            let nextId = String(courseId || '').trim();
            let nextName = String(courseName || '').trim();
            if (!nextName && nextId) {
                const matched = getCourseById(nextId);
                nextName = matched ? String(matched.name || '').trim() : nextId;
            }
            if (!nextId && nextName) {
                const matched = managerCourses.find((item) => String(item.name || '').trim() === nextName);
                nextId = matched ? String(matched.id || '').trim() : nextName;
            }
            if (!nextName && nextId && courseSelect) {
                const selectedOption = Array.from(courseSelect.options || []).find((option) => String(option.value || '').trim() === nextId);
                if (selectedOption) {
                    nextName = String(selectedOption.textContent || '').trim();
                }
            }

            selectedCourseId = nextId;
            selectedCourseName = nextName;

            if (courseSelect) {
                courseSelect.value = nextId;
            }
            if (courseCurrentLine) {
                courseCurrentLine.textContent = selectedCourseName
                    ? `目前課程：${selectedCourseName}`
                    : '目前課程：未選擇';
            }

            if (persist) {
                try {
                    if (selectedCourseId) {
                        window.localStorage.setItem(COURSE_STORAGE_KEY, selectedCourseId);
                    } else {
                        window.localStorage.removeItem(COURSE_STORAGE_KEY);
                    }
                } catch (error) {
                    console.warn('Unable to persist selected course.', error);
                }
            }

            syncAttendanceButtonAvailability();
        }

        function initializeCoursePicker() {
            if (!courseSelect) {
                return;
            }

            const courseOptions = managerCourses.map(
                (item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`
            );
            if (courseOptions.length) {
                courseSelect.innerHTML = courseOptions.join('');
                courseSelect.disabled = false;
            } else {
                courseSelect.innerHTML = '<option value="">請先選擇課程</option>';
                courseSelect.disabled = true;
            }

            if (coursePickerShell) {
                coursePickerShell.classList.toggle('is-empty', managerCourses.length === 0);
            }

            let initialCourse = null;
            try {
                const savedCourseId = window.localStorage.getItem(COURSE_STORAGE_KEY) || '';
                if (savedCourseId) {
                    initialCourse = getCourseById(savedCourseId);
                }
            } catch (error) {
                initialCourse = null;
            }

            if (!initialCourse && defaultCourseId) {
                initialCourse = getCourseById(defaultCourseId);
            }
            if (!initialCourse && defaultCourseName) {
                initialCourse = managerCourses.find((item) => String(item.name || '').trim() === String(defaultCourseName).trim()) || null;
            }
            if (!initialCourse && managerCourses.length === 1) {
                initialCourse = managerCourses[0];
            }

            if (initialCourse) {
                setSelectedCourse(initialCourse.id, initialCourse.name, false);
            } else {
                setSelectedCourse('', '', false);
            }
            syncSelectedCourseToServer();

            courseSelect.addEventListener('change', (event) => {
                const nextId = String(event.target.value || '').trim();
                const matched = getCourseById(nextId);
                setSelectedCourse(nextId, matched ? matched.name : '', true);
                syncSelectedCourseToServer();
            });
        }

        function setProfileMenuOpen(isOpen) {
            if (!profileMenu || !profileMenuButton) {
                return;
            }
            profileMenu.classList.toggle('is-open', isOpen);
            profileMenuButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            if (!isOpen) {
                profileMenu.classList.remove('is-hover-mark');
                setAlertPanelOpen(false);
            }
        }

        function setAlertPanelOpen(isOpen) {
            if (!profileAlertAnchor || !alertBellButton) {
                return;
            }
            profileAlertAnchor.classList.toggle('is-open', isOpen);
            alertBellButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        }

        function setTeacherChatOpen(isOpen, options = {}) {
            if (!teacherChatWidget || !teacherChatToggle) {
                return;
            }
            teacherChatWidget.classList.toggle('is-open', isOpen);
            teacherChatToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            if (isOpen && options.focusInput && teacherChatInput) {
                window.setTimeout(() => {
                    teacherChatInput.focus();
                }, 40);
            }
        }

        function appendChatMessage(name, text, source = 'system') {
            if (!teacherChatBody) {
                return;
            }
            const wrapper = document.createElement('div');
            wrapper.className = `chat-message ${source === 'teacher' ? 'from-teacher' : 'from-system'}`;
            const nameLine = document.createElement('span');
            nameLine.className = 'chat-name';
            nameLine.textContent = name;
            const content = document.createElement('p');
            content.textContent = text;
            wrapper.append(nameLine, content);
            teacherChatBody.appendChild(wrapper);
            teacherChatBody.scrollTop = teacherChatBody.scrollHeight;
        }

        function buildMockChatReply(inputText) {
            const message = String(inputText || '').trim();
            if (!message) {
                return '目前課堂指標都在可接受範圍內，若要我鎖定特定學生可直接輸入姓名。';
            }
            if (message.includes('楊翔順') || message.includes('YShane11')) {
                return '楊翔順目前在畫面中央，專注度 58%，頭部穩定度正常，距離約 72 cm。';
            }
            if (message.includes('專注') || message.toLowerCase().includes('focus')) {
                return '目前全班專注度中位數約 61%，有 2 位低於 50%，建議安排一次短互動提問。';
            }
            if (message.includes('出席') || message.includes('在場')) {
                return '目前已確認 6 人在場，暫離 1 人，系統會持續追蹤回到畫面的時間點。';
            }
            if (message.includes('提醒') || message.includes('警示')) {
                return '最新警示為「低專注」與「長時間低頭」，已同步顯示在右上提醒清單。';
            }
            const cannedReplies = [
                '收到，我會持續觀察這位學生接下來 2 分鐘的變化並更新你。',
                '目前看起來數值正常，如果你要我鎖定某一項指標可以直接說。',
                '已幫你記下這個關注項目，下一次波動時我會優先提醒。',
            ];
            const replyIndex = hashSeed(`${message}-${Date.now()}`) % cannedReplies.length;
            return cannedReplies[replyIndex];
        }

        function submitTeacherChatMessage() {
            if (!teacherChatInput) {
                return;
            }
            const message = String(teacherChatInput.value || '').trim();
            if (!message) {
                return;
            }
            appendChatMessage('老師', message, 'teacher');
            teacherChatInput.value = '';
            const reply = buildMockChatReply(message);
            window.setTimeout(() => {
                appendChatMessage('課堂助教', reply, 'system');
            }, 260);
        }

        function clearProfileMenuCloseTimer() {
            if (!profileMenuCloseTimer) {
                return;
            }
            window.clearTimeout(profileMenuCloseTimer);
            profileMenuCloseTimer = null;
        }

        function scheduleProfileMenuClose() {
            clearProfileMenuCloseTimer();
            profileMenuCloseTimer = window.setTimeout(() => {
                profileMenuCloseTimer = null;
                const panelHovered = profilePanel?.matches(':hover');
                const markHovered = profileMark?.matches(':hover');
                const panelFocused = profileMenu?.contains(document.activeElement);
                if (!panelHovered && !markHovered && !panelFocused) {
                    profileMenu?.classList.remove('is-hover-mark');
                    setProfileMenuOpen(false);
                }
            }, PROFILE_MENU_CLOSE_DELAY_MS);
        }

        function formatDuration(seconds) {
            const totalSeconds = Math.max(0, Math.round(Number(seconds || 0)));
            const minutes = Math.floor(totalSeconds / 60);
            const remainder = totalSeconds % 60;
            return `${minutes}m ${String(remainder).padStart(2, '0')}s`;
        }

        function hashSeed(value) {
            const text = String(value || 'student');
            let hash = 0;
            for (let index = 0; index < text.length; index += 1) {
                hash = ((hash << 5) - hash) + text.charCodeAt(index);
                hash |= 0;
            }
            return Math.abs(hash);
        }

        function parseCsvRows(csvText) {
            const lines = String(csvText || '')
                .trim()
                .split(/\r?\n/)
                .filter(Boolean);
            if (lines.length <= 1) {
                return [];
            }

            const headers = lines[0].split(',').map((item) => item.trim());
            return lines.slice(1).map((line) => {
                const values = line.split(',').map((item) => item.trim());
                return headers.reduce((record, header, index) => {
                    record[header] = values[index] ?? '';
                    return record;
                }, {});
            });
        }

        async function loadMockMetricDataset(key) {
            if (mockMetricCache.has(key)) {
                return mockMetricCache.get(key);
            }

            const response = await fetch(`${MOCK_METRIC_CSV_BASE}${key}.csv`, { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`Unable to load mock metric CSV: ${key}`);
            }

            const rows = parseCsvRows(await response.text());
            mockMetricCache.set(key, rows);
            return rows;
        }

        function pseudoRandom(seed, index = 0) {
            const raw = Math.sin((seed + 1) * 12.9898 + (index + 1) * 78.233) * 43758.5453;
            return raw - Math.floor(raw);
        }

        function pickWeightedIndex(weights, seed, index = 0) {
            const safeWeights = weights.map((value) => Math.max(0, Number(value || 0)));
            const total = safeWeights.reduce((sum, value) => sum + value, 0);
            if (!total) {
                return 0;
            }

            let threshold = pseudoRandom(seed, index) * total;
            for (let itemIndex = 0; itemIndex < safeWeights.length; itemIndex += 1) {
                threshold -= safeWeights[itemIndex];
                if (threshold <= 0) {
                    return itemIndex;
                }
            }
            return Math.max(0, safeWeights.length - 1);
        }

        function isHistoryMetric(key) {
            return METRIC_HISTORY_KEYS.has(key);
        }

        function isLiveClassroomMetric(key) {
            return LIVE_CLASSROOM_METRIC_KEYS.has(key);
        }

        function normalizeMetricRow(row) {
            const safeTime = String(row?.time || row?.recorded_at || '').trim();
            const safeLabel = String(row?.label || safeTime || '').trim();
            const rawValue = row?.value;
            const numericValue = Number(rawValue);
            return {
                time: safeTime || nowTimeLabel(),
                label: safeLabel || (safeTime || nowTimeLabel()),
                value: Number.isFinite(numericValue) ? numericValue : (rawValue ?? 0),
            };
        }

        function normalizeMetricRows(rows) {
            if (!Array.isArray(rows)) {
                return [];
            }
            return rows.map((row) => normalizeMetricRow(row));
        }

        function buildRecentWeekLabels(count) {
            const safeCount = Math.max(1, Number(count) || 1);
            const now = new Date();
            return Array.from({ length: safeCount }, (_, index) => {
                const date = new Date(now);
                date.setDate(now.getDate() - ((safeCount - index - 1) * 7));
                return `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
            });
        }

        function buildAttendanceHistoryRows(seedRows, studentKey) {
            const count = Math.max(4, seedRows.length || 6);
            const labels = buildRecentWeekLabels(count);
            const seed = hashSeed(`${studentKey}-attendance-rate-${buildLocalDateString()}`);
            const basePresentChance = 0.82 + (pseudoRandom(seed, 2) * 0.14);
            const rows = labels.map((label, index) => {
                const value = index === labels.length - 1
                    ? 100
                    : (pseudoRandom(seed, index + 31) <= Math.max(0.72, Math.min(0.96, basePresentChance + ((pseudoRandom(seed, index + 11) - 0.5) * 0.08))) ? 100 : 0);
                return { time: label, label, value };
            });

            const absentIndexes = rows
                .map((row, index) => ({ row, index }))
                .filter((item) => item.index < rows.length - 1 && Number(item.row.value || 0) <= 0)
                .map((item) => item.index);
            while (absentIndexes.length > 2) {
                rows[absentIndexes.shift()].value = 100;
            }
            return rows;
        }

        function buildAssignmentScoreRows(seedRows, studentKey) {
            const count = Math.max(4, seedRows.length || 6);
            const labels = buildRecentWeekLabels(count);
            const attendanceRows = buildAttendanceHistoryRows(seedRows, studentKey);
            const seed = hashSeed(`${studentKey}-assignment-score-${buildLocalDateString()}`);
            const attendanceRate = attendanceRows.reduce((sum, row) => sum + Number(row.value || 0), 0) / Math.max(1, count * 100);
            const baseScore = 72 + (attendanceRate * 15) + (pseudoRandom(seed, 3) * 7);
            return labels.map((label, index) => {
                const progress = index / Math.max(1, count - 1);
                const trend = (progress - 0.5) * (pseudoRandom(seed, 7) * 6);
                const noise = (pseudoRandom(seed, index + 17) - 0.5) * 9;
                const absencePenalty = Number(attendanceRows[index]?.value || 0) <= 0 ? 4 : 0;
                const score = Math.max(68, Math.min(98, baseScore + trend + noise - absencePenalty));
                return {
                    time: label,
                    label,
                    value: Math.round(score),
                };
            });
        }

        function buildNumericHistoryRows(key, seedRows, studentKey) {
            const safeRows = seedRows.length ? seedRows : [{ value: 50 }];
            const timeLabels = buildRecentTimeLabels(METRIC_HISTORY_SECONDS);
            const seed = hashSeed(`${studentKey}-${key}`);
            const waveScaleMap = {
                'focus-ratio': 6.8,
                'head-stability': 3.2,
                'fatigue': 6.2,
                'posture-angle': 2.8,
                'desk-distance': 4.6,
                'stillness': 2.8,
            };
            const jitterScaleMap = {
                'focus-ratio': 3.8,
                'head-stability': 1.6,
                'fatigue': 3.4,
                'posture-angle': 1.4,
                'desk-distance': 2.1,
                'stillness': 1.6,
            };
            const waveScale = waveScaleMap[key] ?? 4.6;
            const jitterScale = jitterScaleMap[key] ?? 2.4;
            const precision = key === 'head-stability' ? 0 : 1;

            return timeLabels.map((time, index) => {
                const base = Number(safeRows[index % safeRows.length].value || safeRows[safeRows.length - 1].value || 0);
                const wave = Math.sin((index / 15) + (seed % 13)) * waveScale;
                const jitter = (pseudoRandom(seed, index) - 0.5) * jitterScale;
                const value = clampMetricValue(key, base + wave + jitter);
                return {
                    time,
                    label: time,
                    value: Number(value.toFixed(precision)),
                };
            });
        }

        function buildHandRaiseHistoryRows(seedRows, studentKey) {
            const safeRows = seedRows.length ? seedRows : [{ value: 4 }];
            const timeLabels = buildRecentTimeLabels(METRIC_HISTORY_SECONDS);
            const seed = hashSeed(`${studentKey}-hand-raise`);
            return timeLabels.map((time, index) => {
                const base = Number(safeRows[index % safeRows.length].value || 0);
                const chance = Math.min(0.14, Math.max(0.015, base / 95));
                const raised = pseudoRandom(seed, index) < chance ? 1 : 0;
                return {
                    time,
                    label: time,
                    value: raised,
                };
            });
        }

        function buildCategoryHistoryRows(seedRows, studentKey) {
            const safeRows = seedRows.length ? seedRows : [{ label: '未分類', value: 1 }];
            const labels = safeRows.map((row) => row.label || '未分類');
            const weights = safeRows.map((row) => Number(row.value || 0));
            const timeLabels = buildRecentTimeLabels(METRIC_HISTORY_SECONDS);
            const seed = hashSeed(`${studentKey}-shared-attention`);
            let currentIndex = pickWeightedIndex(weights, seed, 0);

            return timeLabels.map((time, index) => {
                if (index === 0 || pseudoRandom(seed, index + 31) > 0.72) {
                    currentIndex = pickWeightedIndex(weights, seed, index + 7);
                }
                return {
                    time,
                    label: labels[currentIndex] || '未分類',
                    value: 1,
                };
            });
        }

        function buildMetricHistoryRows(key, seedRows, studentKey, type) {
            if (key === 'assignment-score') {
                return buildAssignmentScoreRows(seedRows, studentKey);
            }
            if (key === 'attendance-rate') {
                return buildAttendanceHistoryRows(seedRows, studentKey);
            }
            if (!isHistoryMetric(key)) {
                return seedRows.map((row) => ({ ...row }));
            }
            if (type === 'pie') {
                return buildCategoryHistoryRows(seedRows, studentKey);
            }
            if (key === 'hand-raise') {
                return buildHandRaiseHistoryRows(seedRows, studentKey);
            }
            return buildNumericHistoryRows(key, seedRows, studentKey);
        }

        function buildMetricBuckets(rows, bucketCount = METRIC_BUCKET_COUNT) {
            const safeRows = Array.isArray(rows) ? rows : [];
            const buckets = [];
            for (let index = 0; index < bucketCount; index += 1) {
                const start = Math.floor((index * safeRows.length) / bucketCount);
                const end = Math.floor(((index + 1) * safeRows.length) / bucketCount);
                const segment = safeRows.slice(start, end);
                if (segment.length) {
                    buckets.push(segment);
                }
            }
            return buckets;
        }

        function buildDisplayMetricRows(key, rows, type) {
            const safeRows = Array.isArray(rows) ? rows : [];
            if (!safeRows.length) {
                return [];
            }

            if (PERSONAL_EXPORT_HISTORY_METRIC_KEYS.includes(key)) {
                return safeRows;
            }

            if (!isHistoryMetric(key)) {
                return safeRows;
            }

            const buildWindowedRows = (targetCount, aggregateFn) => {
                const count = Math.max(1, Math.min(targetCount, safeRows.length));
                if (count === 1) {
                    const only = safeRows[safeRows.length - 1];
                    return [{ label: only.time || only.label || '--', value: aggregateFn([only]) }];
                }
                const denominator = Math.max(count - 1, 1);
                const windows = [];
                for (let slot = 0; slot < count; slot += 1) {
                    const startIndex = Math.round((slot * (safeRows.length - 1)) / denominator);
                    const endIndex = slot === count - 1
                        ? safeRows.length - 1
                        : Math.round(((slot + 1) * (safeRows.length - 1)) / denominator);
                    const sliceEnd = Math.max(startIndex + 1, endIndex + 1);
                    const segment = safeRows.slice(startIndex, sliceEnd);
                    if (!segment.length) {
                        continue;
                    }
                    const tail = segment[segment.length - 1];
                    windows.push({
                        label: tail.time || tail.label || '--',
                        value: aggregateFn(segment),
                    });
                }
                return windows;
            };

            if (type === 'line') {
                const precision = key === 'head-stability' ? 0 : 1;
                return buildWindowedRows(METRIC_LINE_DISPLAY_POINTS, (segment) => {
                    const total = segment.reduce((sum, row) => sum + Number(row.value || 0), 0);
                    const average = total / Math.max(segment.length, 1);
                    return Number(average.toFixed(precision));
                });
            }

            if (type === 'bar') {
                return buildWindowedRows(METRIC_BUCKET_COUNT, (segment) => {
                    const total = segment.reduce((sum, row) => sum + Number(row.value || 0), 0);
                    const aggregatedValue = key === 'hand-raise'
                        ? total
                        : (total / Math.max(segment.length, 1));
                    return Number(aggregatedValue.toFixed(key === 'hand-raise' ? 0 : 1));
                });
            }

            if (type === 'pie') {
                const grouped = new Map();
                safeRows.forEach((row) => {
                    const label = String(row.label || '未分類').trim() || '未分類';
                    grouped.set(label, (grouped.get(label) || 0) + 1);
                });
                return Array.from(grouped.entries()).map(([label, value]) => ({ label, value }));
            }

            return safeRows;
        }

        function scaleValue(value, min, max, outMin, outMax) {
            if (max === min) {
                return (outMin + outMax) / 2;
            }
            return outMax - (((value - min) / (max - min)) * (outMax - outMin));
        }

        function formatMetricNumber(value, digits = 1) {
            return Number(value || 0).toFixed(digits).replace(/\.0$/, '');
        }

        function metricDigits(key) {
            return key === 'assignment-score' || key === 'attendance-rate' || key === 'hand-raise' || key === 'head-stability' ? 0 : 1;
        }

        function metricUnit(key) {
            const unitMap = {
                'assignment-score': '分',
                'attendance-rate': '%',
                'focus-ratio': '%',
                'fatigue': '%',
                'posture-angle': '°',
                'desk-distance': 'cm',
                'stillness': '%',
                'hand-raise': '次',
            };
            return unitMap[key] ?? '';
        }

        function formatMetricValue(key, value) {
            const unit = metricUnit(key);
            const separator = unit && !['%', '°'].includes(unit) ? ' ' : '';
            return `${formatMetricNumber(value, metricDigits(key))}${separator}${unit}`;
        }

        function hexToRgba(hex, alpha) {
            const raw = String(hex || '#4ea1ff').replace('#', '');
            const normalized = raw.length === 3
                ? raw.split('').map((char) => char + char).join('')
                : raw;
            const red = parseInt(normalized.slice(0, 2), 16);
            const green = parseInt(normalized.slice(2, 4), 16);
            const blue = parseInt(normalized.slice(4, 6), 16);
            return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
        }

        function buildSmoothPath(points) {
            if (!points.length) {
                return '';
            }
            if (points.length === 1) {
                return `M ${points[0].x} ${points[0].y}`;
            }

            let path = `M ${points[0].x} ${points[0].y}`;
            for (let index = 1; index < points.length; index += 1) {
                const previous = points[index - 1];
                const current = points[index];
                const midX = (previous.x + current.x) / 2;
                path += ` C ${midX} ${previous.y}, ${midX} ${current.y}, ${current.x} ${current.y}`;
            }
            return path;
        }

        function buildTickValues(min, max, steps = 4) {
            const values = [];
            for (let index = 0; index < steps; index += 1) {
                const ratio = index / Math.max(steps - 1, 1);
                values.push(max - ((max - min) * ratio));
            }
            return values;
        }

        function buildLabelIndexes(length, limit = 4) {
            if (length <= 0) {
                return [];
            }

            if (length <= limit) {
                return Array.from({ length }, (_, index) => index);
            }

            const indexes = new Set([0, length - 1]);
            const slots = Math.max(limit - 1, 1);
            for (let step = 1; step < slots; step += 1) {
                indexes.add(Math.round((step * (length - 1)) / slots));
            }
            return Array.from(indexes).sort((left, right) => left - right);
        }

        function shouldHideMetricLabels(key) {
            return false;
        }

        function formatMetricLabel(key, label) {
            const safeLabel = String(label || '').trim();
            if (!safeLabel) {
                return '--';
            }

            if (shouldHideMetricLabels(key)) {
                return '';
            }

            if (key === 'shared-attention') {
                if (safeLabel.includes('老師')) {
                    return '看老師';
                }
                if (safeLabel.includes('同學')) {
                    return '看同學';
                }
                if (safeLabel.includes('別') || safeLabel.includes('其他')) {
                    return '看別處';
                }
            }

            return safeLabel;
        }

        function buildChartXAxisLabels(labels, chartLeft, chartRight, y, key, limit = 4) {
            const indexes = buildLabelIndexes(labels.length, limit);
            const stepWidth = (chartRight - chartLeft) / Math.max(labels.length - 1, 1);
            return indexes.map((index) => {
                const x = chartLeft + (index * stepWidth);
                return `<text class="chart-x-label" x="${x.toFixed(2)}" y="${y}" text-anchor="middle">${escapeHtml(formatMetricLabel(key, labels[index]))}</text>`;
            }).join('');
        }

        function formatTimeLabel(date) {
            return date.toLocaleTimeString('zh-TW', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
            });
        }

        function nowTimeLabel() {
            return formatTimeLabel(new Date());
        }

        function buildRecentTimeLabels(count) {
            const safeCount = Math.max(0, Number(count) || 0);
            const now = Date.now();
            return Array.from({ length: safeCount }, (_, index) => {
                const offset = (safeCount - index - 1) * 1000;
                return formatTimeLabel(new Date(now - offset));
            });
        }

        function buildLineMetricChart(accent, rows, key) {
            const values = rows.map((row) => Number(row.value || 0));
            const labels = rows.map((row) => row.label || row.time || '');
            const chartLeft = 44;
            const chartRight = 294;
            const chartTop = 24;
            const chartBottom = 146;
            const safeMin = Math.min(...values);
            const safeMax = Math.max(...values);
            const padding = Math.max((safeMax - safeMin) * 0.18, 4);
            const min = Math.max(0, safeMin - padding);
            const max = safeMax + padding;
            const points = values.map((value, index) => {
                const x = chartLeft + (index * ((chartRight - chartLeft) / Math.max(values.length - 1, 1)));
                const y = scaleValue(value, min, max, chartTop, chartBottom);
                return { x: Number(x.toFixed(2)), y: Number(y.toFixed(2)) };
            });
            const path = buildSmoothPath(points);
            const areaPath = `${path} L ${chartRight} ${chartBottom} L ${chartLeft} ${chartBottom} Z`;
            const tickValues = buildTickValues(min, max, 4);
            const tickLines = tickValues.map((tick) => {
                const y = scaleValue(tick, min, max, chartTop, chartBottom);
                return `
                    <line x1="${chartLeft}" y1="${y.toFixed(2)}" x2="${chartRight}" y2="${y.toFixed(2)}"></line>
                    <text class="chart-tick-label" x="${chartLeft - 8}" y="${(y + 3).toFixed(2)}" text-anchor="end">${formatMetricNumber(tick)}</text>
                `;
            }).join('');
            const xLabels = buildChartXAxisLabels(labels, chartLeft, chartRight, chartBottom + 24, key, 4);

            const axisStart = labels[0] || '';
            const axisEnd = labels[labels.length - 1] || '';
            const current = values[values.length - 1] || 0;
            const average = values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);
            const gradientId = `line-gradient-${key}`;
            const summaryText = `最新 ${formatMetricValue(key, current)} / 平均 ${formatMetricValue(key, average)}`;
            const sublineLeft = `區間 ${formatMetricValue(key, safeMin)} - ${formatMetricValue(key, safeMax)}`;
            const sublineRight = `${formatMetricLabel(key, axisStart)} 至 ${formatMetricLabel(key, axisEnd)}`;

            return `
                <svg viewBox="0 0 320 190" preserveAspectRatio="xMidYMid meet">
                    <defs>
                        <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="${hexToRgba(accent, 0.42)}"></stop>
                            <stop offset="100%" stop-color="${hexToRgba(accent, 0)}"></stop>
                        </linearGradient>
                    </defs>
                    <g class="chart-grid-lines">
                        ${tickLines}
                    </g>
                    <path class="chart-area-fill" d="${areaPath}" fill="url(#${gradientId})"></path>
                    <line class="chart-axis-line" x1="${chartLeft}" y1="${chartBottom}" x2="${chartRight}" y2="${chartBottom}"></line>
                    <line class="chart-axis-line" x1="${chartLeft}" y1="${chartTop}" x2="${chartLeft}" y2="${chartBottom}"></line>
                    <path class="chart-focus-line" d="${path}" fill="none" stroke="${accent}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>
                    ${points.map((point, index) => index === points.length - 1 ? `<circle class="chart-point" cx="${point.x}" cy="${point.y}" r="4.5" fill="${accent}"></circle>` : '').join('')}
                    ${xLabels}
                </svg>
                <div class="chart-live-summary">${summaryText}</div>
                <div class="chart-live-subline"><span>${sublineLeft}</span><span>${sublineRight}</span></div>
            `;
        }

        function buildBarMetricChart(accent, rows, key) {
            const values = rows.map((row) => Number(row.value || 0));
            const labels = rows.map((row) => row.label || '');
            const chartLeft = 42;
            const chartRight = 294;
            const chartTop = 24;
            const chartBottom = 146;
            const max = Math.max(...values, 1);
            const tickValues = buildTickValues(0, max, 4);
            const barGap = (chartRight - chartLeft) / Math.max(values.length, 1);
            const bars = values.map((value, index) => {
                const x = chartLeft + 8 + (index * barGap);
                const height = ((value / max) * (chartBottom - chartTop));
                const y = chartBottom - height;
                const width = Math.max(16, barGap - 18);
                const centerX = x + (width / 2);
                const valueY = Math.max(chartTop + 10, y - 8);
                return `
                    <rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${width.toFixed(2)}" height="${height.toFixed(2)}" rx="9" fill="${accent}" opacity="${Math.min(0.76 + (index * 0.05), 1)}"></rect>
                    <text class="chart-bar-value" x="${centerX.toFixed(2)}" y="${valueY.toFixed(2)}" text-anchor="middle">${formatMetricValue(key, value)}</text>
                    <text class="chart-x-label" x="${centerX.toFixed(2)}" y="${(chartBottom + 24).toFixed(2)}" text-anchor="middle">${escapeHtml(formatMetricLabel(key, labels[index]))}</text>
                `;
            }).join('');
            const grid = tickValues.map((tick) => {
                const y = scaleValue(tick, 0, max, chartTop, chartBottom);
                return `
                    <line x1="${chartLeft}" y1="${y.toFixed(2)}" x2="${chartRight}" y2="${y.toFixed(2)}"></line>
                    <text class="chart-tick-label" x="${chartLeft - 8}" y="${(y + 3).toFixed(2)}" text-anchor="end">${formatMetricNumber(tick)}</text>
                `;
            }).join('');
            const maxIndex = values.indexOf(Math.max(...values));
            const average = values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);
            const presentDays = values.filter((value) => value >= 50).length;
            const attendanceRate = ((presentDays / Math.max(values.length, 1)) * 100);
            const summaryText = key === 'attendance-rate'
                ? `出席 ${presentDays} / ${values.length} 天`
                : (key === 'assignment-score'
                    ? `最高 ${formatMetricValue(key, values[maxIndex])}`
                : (shouldHideMetricLabels(key)
                    ? `最高 ${formatMetricValue(key, values[maxIndex])}`
                    : `最高 ${formatMetricLabel(key, labels[maxIndex])} ${formatMetricValue(key, values[maxIndex])}`));
            const sublineLeft = key === 'attendance-rate'
                ? `整體出席率 ${formatMetricNumber(attendanceRate)}%`
                : `平均 ${formatMetricValue(key, average)}`;
            const sublineRight = `${values.length} 筆資料`;

            return `
                <svg viewBox="0 0 320 190" preserveAspectRatio="xMidYMid meet">
                    <g class="chart-grid-lines">
                        ${grid}
                    </g>
                    <line class="chart-axis-line" x1="${chartLeft}" y1="${chartBottom}" x2="${chartRight}" y2="${chartBottom}"></line>
                    <line class="chart-axis-line" x1="${chartLeft}" y1="${chartTop}" x2="${chartLeft}" y2="${chartBottom}"></line>
                    ${bars}
                </svg>
                <div class="chart-live-summary">${summaryText}</div>
                <div class="chart-live-subline"><span>${sublineLeft}</span><span>${sublineRight}</span></div>
            `;
        }

        function buildPieMetricChart(accent, rows, key) {
            const values = rows.map((row) => Number(row.value || 0));
            const labels = rows.map((row) => row.label || '');
            const total = values.reduce((sum, value) => sum + value, 0) || 1;
            const palette = [accent, '#1fc7d4', '#7b92ff', '#22c55e'];
            const pieCenterX = 82;
            const pieCenterY = 96;
            const pieRadius = 46;
            const legendDotX = 168;
            const legendLabelX = 182;
            const legendValueX = 312;
            let dashOffset = 0;
            const arcs = values.map((value, index) => {
                const ratio = (value / total) * 360;
                const dashArray = `${Math.max(ratio, 18)} ${360 - Math.max(ratio, 18)}`;
                const arc = `<circle cx="${pieCenterX}" cy="${pieCenterY}" r="${pieRadius}" fill="none" stroke="${palette[index % palette.length]}" stroke-width="22" stroke-linecap="round" stroke-dasharray="${dashArray}" stroke-dashoffset="-${dashOffset}" transform="rotate(-90 ${pieCenterX} ${pieCenterY})"></circle>`;
                dashOffset += ratio + 10;
                return arc;
            }).join('');
            const legend = labels.map((label, index) => {
                const y = 54 + (index * 34);
                const percent = ((values[index] / total) * 100);
                const compactLabel = formatMetricLabel(key, label).slice(0, 6);
                return `
                    <circle cx="${legendDotX}" cy="${y}" r="5.5" fill="${palette[index % palette.length]}"></circle>
                    <text class="chart-legend-label" x="${legendLabelX}" y="${y + 4}">${escapeHtml(compactLabel)}</text>
                    <text class="chart-legend-value" x="${legendValueX}" y="${y + 4}" text-anchor="end">${formatMetricNumber(percent)}%</text>
                `;
            }).join('');
            const topIndex = values.indexOf(Math.max(...values));
            const topRatio = (values[topIndex] / total) * 100;
            const centerText = formatMetricLabel(key, labels[topIndex]);
            return `
                <svg viewBox="0 0 320 190" preserveAspectRatio="xMidYMid meet">
                    <circle cx="${pieCenterX}" cy="${pieCenterY}" r="${pieRadius}" fill="none" stroke="rgba(122,142,182,0.18)" stroke-width="22"></circle>
                    ${arcs}
                    ${legend}
                    <text class="chart-axis-label" x="${pieCenterX}" y="92" text-anchor="middle">${escapeHtml(centerText)}</text>
                    <text class="chart-tick-label" x="${pieCenterX}" y="110" text-anchor="middle">${formatMetricNumber(topRatio)}%</text>
                </svg>
                <div class="chart-live-summary">主要分布 ${centerText || '--'} ${formatMetricNumber(topRatio)}%</div>
                <div class="chart-live-subline"><span>共 ${labels.length} 類資料</span><span>分類占比</span></div>
            `;
        }

        function buildMetricChart(type, accent, rows, key) {
            if (type === 'pie') {
                return buildPieMetricChart(accent, rows, key);
            }
            if (type === 'bar') {
                return buildBarMetricChart(accent, rows, key);
            }
            return buildLineMetricChart(accent, rows, key);
        }

        function buildLiveMetricRows(key, rows, studentKey, type) {
            return buildMetricHistoryRows(key, rows, studentKey, type);
        }

        async function prepareStudentMetricState(studentKey, selectedPerson = null) {
            if (currentMetricStudentKey === studentKey && liveMetricState.size) {
                if (selectedPerson) {
                    LIVE_CLASSROOM_METRIC_KEYS.forEach((key) => {
                        const sourceRows = selectedPerson?.classroom_metrics?.[key] || [];
                        liveMetricState.set(key, normalizeMetricRows(sourceRows));
                    });
                }
                return;
            }

            currentMetricStudentKey = studentKey;
            liveMetricState.clear();

            await Promise.all(Array.from(studentMetricCharts).map(async (node, index) => {
                const key = node.dataset.chartKey || `metric-${index}`;
                const type = node.dataset.chartType || 'line';
                if (isLiveClassroomMetric(key)) {
                    const sourceRows = selectedPerson?.classroom_metrics?.[key] || [];
                    liveMetricState.set(key, normalizeMetricRows(sourceRows));
                    return;
                }
                const rows = await loadMockMetricDataset(key);
                liveMetricState.set(key, buildLiveMetricRows(key, rows, studentKey, type));
            }));
        }

        function clampMetricValue(key, value) {
            const rangeMap = {
                'assignment-score': [60, 100],
                'attendance-rate': [65, 100],
                'focus-ratio': [45, 100],
                'head-stability': [8, 38],
                'fatigue': [5, 75],
                'posture-angle': [4, 18],
                'desk-distance': [30, 95],
                'stillness': [5, 45],
                'hand-raise': [0, 10],
                'shared-attention': [8, 80],
            };
            const [min, max] = rangeMap[key] || [0, 100];
            return Math.max(min, Math.min(max, value));
        }

        function buildNextNumericMetricValue(key, previousValue) {
            const driftMap = {
                'focus-ratio': 3.8,
                'head-stability': 1.4,
                'fatigue': 3.6,
                'posture-angle': 1.2,
                'desk-distance': 2.2,
                'stillness': 2.0,
            };
            const precision = key === 'head-stability' ? 0 : 1;
            const drift = driftMap[key] ?? 2.4;
            const nextValue = clampMetricValue(key, Number(previousValue || 0) + ((Math.random() * drift * 2) - drift));
            return Number(nextValue.toFixed(precision));
        }

        function buildNextHandRaiseValue(rows) {
            const recentWindow = rows.slice(-60);
            const recentCount = recentWindow.reduce((sum, row) => sum + Number(row.value || 0), 0);
            const chance = Math.min(0.16, Math.max(0.015, (recentCount + 1) / 85));
            return Math.random() < chance ? 1 : 0;
        }

        function buildNextCategoryLabel(rows) {
            const counts = new Map();
            rows.forEach((row) => {
                const label = String(row.label || '未分類').trim() || '未分類';
                counts.set(label, (counts.get(label) || 0) + 1);
            });
            const entries = Array.from(counts.entries());
            if (!entries.length) {
                return '未分類';
            }
            const total = entries.reduce((sum, [, value]) => sum + value, 0);
            let threshold = Math.random() * total;
            for (const [label, value] of entries) {
                threshold -= value;
                if (threshold <= 0) {
                    return label;
                }
            }
            return entries[entries.length - 1][0];
        }

        function tickStudentMetricState() {
            liveMetricState.forEach((rows, key) => {
                if (!rows.length) {
                    return;
                }
                if (isLiveClassroomMetric(key)) {
                    return;
                }

                const type = Array.from(studentMetricCharts).find((node) => node.dataset.chartKey === key)?.dataset.chartType || 'line';
                if (!isHistoryMetric(key)) {
                    return;
                }

                if (type === 'line') {
                    const previousRow = rows[rows.length - 1];
                    const nextLabel = nowTimeLabel();
                    rows.shift();
                    rows.push({
                        ...previousRow,
                        time: nextLabel,
                        label: nextLabel,
                        value: buildNextNumericMetricValue(key, previousRow.value),
                    });
                    return;
                }

                if (type === 'bar' && (key === 'stillness' || key === 'hand-raise')) {
                    const previousRow = rows[rows.length - 1];
                    const nextLabel = nowTimeLabel();
                    rows.shift();
                    rows.push({
                        ...previousRow,
                        time: nextLabel,
                        label: nextLabel,
                        value: key === 'hand-raise'
                            ? buildNextHandRaiseValue(rows)
                            : buildNextNumericMetricValue(key, previousRow.value),
                    });
                    return;
                }

                if (type === 'pie' && key === 'shared-attention') {
                    const nextLabel = nowTimeLabel();
                    rows.shift();
                    rows.push({
                        time: nextLabel,
                        label: buildNextCategoryLabel(rows),
                        value: 1,
                    });
                }
            });
        }

        async function renderStudentMetricCharts() {
            await Promise.all(Array.from(studentMetricCharts).map(async (node, index) => {
                const type = node.dataset.chartType || 'line';
                const key = node.dataset.chartKey || `metric-${index}`;
                const accentMap = {
                    'assignment-score': '#4ea1ff',
                    'attendance-rate': '#1fc7d4',
                    'focus-ratio': '#4ea1ff',
                    'head-stability': '#7b92ff',
                    'fatigue': '#f59e0b',
                    'posture-angle': '#38bdf8',
                    'desk-distance': '#06b6d4',
                    'stillness': '#14b8a6',
                    'hand-raise': '#22c55e',
                    'shared-attention': '#4ea1ff',
                };
                const accent = accentMap[key] || '#4ea1ff';
                try {
                    let rawRows = liveMetricState.get(key);
                    if (!rawRows) {
                        rawRows = isLiveClassroomMetric(key)
                            ? []
                            : await loadMockMetricDataset(key);
                    }
                    const rows = buildDisplayMetricRows(key, rawRows, type);
                    if (!rows.length) {
                        node.innerHTML = '<div class="sparkline-placeholder">等待即時資料...</div>';
                        return;
                    }
                    node.innerHTML = buildMetricChart(type, accent, rows, key);
                } catch (error) {
                    node.innerHTML = isLiveClassroomMetric(key)
                        ? '<div class="sparkline-placeholder">等待即時資料...</div>'
                        : `<div class="sparkline-placeholder">無法載入 ${key}.csv</div>`;
                }
            }));
        }

        function getMetricMetadata() {
            return Array.from(studentMetricCharts).reduce((map, node, index) => {
                const key = node.dataset.chartKey || `metric-${index}`;
                const title = node.closest('.student-metric-card')?.querySelector('.student-metric-top strong')?.textContent?.trim() || key;
                map.set(key, {
                    title,
                    chartType: node.dataset.chartType || 'line',
                });
                return map;
            }, new Map());
        }

        function buildCsvCell(value) {
            const safeValue = String(value ?? '');
            if (safeValue.includes(',') || safeValue.includes('"') || safeValue.includes('\n')) {
                return `"${safeValue.replaceAll('"', '""')}"`;
            }
            return safeValue;
        }

        function sanitizeFileNameSegment(value, fallbackValue = '未指定課程') {
            const normalized = String(value ?? '')
                .trim()
                .replace(/[<>:"/\\|?*\u0000-\u001F]/g, '-')
                .replace(/\s+/g, '-')
                .replace(/-+/g, '-')
                .replace(/^-+|-+$/g, '');
            return normalized || fallbackValue;
        }

        function buildLocalDateString() {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }

        function buildMetricExportRows() {
            const metricMetadata = getMetricMetadata();
            const exportRows = [];
            const latestConfirmed = dedupeConfirmedPeople(getLatestConfirmedPeople()).filter(isPresentPerson);
            const exportCourseId = String(selectedCourseId || '').trim();
            const exportCourseName = String(selectedCourseName || '').trim() || '未指定課程';

            latestConfirmed.forEach((person) => {
                const trainingRecord = findTrainingRecord(person);
                const studentId = (trainingRecord && trainingRecord.student_id) || person.student_id || person.user_id || '--';
                const studentName = (trainingRecord && trainingRecord.name) || person.display_name || person.name || '學生';

                if (Array.isArray(person.presence_points)) {
                    person.presence_points.forEach((point) => {
                        exportRows.push({
                            course_id: exportCourseId,
                            course_name: exportCourseName,
                            student_id: studentId,
                            student_name: studentName,
                            metric_key: 'presence',
                            metric_name: '存在時間',
                            chart_type: 'line',
                            recorded_at: formatTimeLabel(new Date(Number(point.t || 0) * 1000)),
                            label: Number(point.v || 0) > 0 ? '在場中' : '已離開',
                            value: Number(point.v || 0),
                        });
                    });
                }

                const classroomMetrics = person.classroom_metrics || {};
                Object.entries(classroomMetrics).forEach(([key, rows]) => {
                    const metadata = metricMetadata.get(key) || { title: key, chartType: key === 'shared-attention' ? 'pie' : 'line' };
                    normalizeMetricRows(rows).forEach((row) => {
                        exportRows.push({
                            course_id: exportCourseId,
                            course_name: exportCourseName,
                            student_id: studentId,
                            student_name: studentName,
                            metric_key: key,
                            metric_name: metadata.title,
                            chart_type: metadata.chartType,
                            recorded_at: row.time || '',
                            label: row.label || '',
                            value: row.value ?? '',
                        });
                    });
                });
            });

            const selectedConfirmedPerson = latestConfirmed.find(
                (person) => String(person.user_id || person.student_id || '').trim() === String(selectedStudentId || '').trim(),
            ) || null;
            if (selectedConfirmedPerson) {
                const selectedTrainingRecord = findTrainingRecord(selectedConfirmedPerson || {});
                const exportStudentId = String(
                    (selectedTrainingRecord && selectedTrainingRecord.student_id)
                    || (selectedConfirmedPerson && (selectedConfirmedPerson.student_id || selectedConfirmedPerson.user_id))
                    || studentSummaryStudentId.textContent.trim()
                    || selectedStudentId
                    || '--',
                ).trim() || '--';
                const exportStudentName = String(
                    (selectedTrainingRecord && selectedTrainingRecord.name)
                    || (selectedConfirmedPerson && (selectedConfirmedPerson.display_name || selectedConfirmedPerson.name))
                    || studentSummaryName.textContent.trim()
                    || studentDetailName.textContent.trim()
                    || '學生',
                ).trim() || '學生';

                PERSONAL_EXPORT_HISTORY_METRIC_KEYS.forEach((key) => {
                    const metadata = metricMetadata.get(key) || { title: key, chartType: 'bar' };
                    const rows = normalizeMetricRows(liveMetricState.get(key) || []);
                    rows.forEach((row) => {
                        exportRows.push({
                            course_id: exportCourseId,
                            course_name: exportCourseName,
                            student_id: exportStudentId,
                            student_name: exportStudentName,
                            metric_key: key,
                            metric_name: metadata.title,
                            chart_type: metadata.chartType,
                            recorded_at: row.time || row.label || '',
                            label: row.label || '',
                            value: row.value ?? '',
                        });
                    });
                });
            }

            return exportRows;
        }

        async function ensurePersonalExportHistoryMetricsLoaded() {
            const studentKey = String(selectedStudentId || currentMetricStudentKey || 'student').trim() || 'student';
            await Promise.all(PERSONAL_EXPORT_HISTORY_METRIC_KEYS.map(async (key) => {
                const existingRows = normalizeMetricRows(liveMetricState.get(key) || []);
                if (existingRows.length) {
                    return;
                }

                let sourceRows = [];
                try {
                    sourceRows = await loadMockMetricDataset(key);
                } catch (error) {
                    sourceRows = [];
                }

                const chartNode = Array.from(studentMetricCharts).find((node) => (node.dataset.chartKey || '') === key);
                const chartType = chartNode?.dataset?.chartType || 'bar';
                const preparedRows = buildLiveMetricRows(key, sourceRows, studentKey, chartType);
                liveMetricState.set(key, normalizeMetricRows(preparedRows));
            }));
        }

        function downloadMetricCsv() {
            const exportRows = buildMetricExportRows();
            if (!exportRows.length) {
                return;
            }

            const headers = ['course_id', 'course_name', 'student_id', 'student_name', 'metric_key', 'metric_name', 'chart_type', 'recorded_at', 'label', 'value'];
            const csvLines = [
                headers.join(','),
                ...exportRows.map((row) => headers.map((header) => buildCsvCell(row[header])).join(',')),
            ];
            const blob = new Blob([`\uFEFF${csvLines.join('\r\n')}`], { type: 'text/csv;charset=utf-8;' });
            const downloadUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            const courseNameForFile = sanitizeFileNameSegment(selectedCourseName || selectedCourseId || '未指定課程', '未指定課程');
            const studentNameForFile = sanitizeFileNameSegment(
                studentSummaryName.textContent.trim() || studentDetailName.textContent.trim() || '學生',
                '學生',
            );
            const dateForFile = buildLocalDateString();
            link.href = downloadUrl;
            link.download = `${studentNameForFile}-${courseNameForFile}-${dateForFile}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(downloadUrl);
        }

        async function handleStudentExportCsv() {
            if (studentExportCsvButton.disabled) {
                return;
            }
            const previousLabel = studentExportCsvButton.textContent;
            studentExportCsvButton.disabled = true;
            studentExportCsvButton.textContent = '匯出中...';
            try {
                await ensurePersonalExportHistoryMetricsLoaded();
                await Promise.resolve().then(() => downloadMetricCsv());
            } finally {
                studentExportCsvButton.textContent = previousLabel || '匯出 CSV';
                studentExportCsvButton.disabled = !(currentView === 'student' && liveMetricState.size);
            }
        }

        function startMetricSimulationLoop() {
            if (metricSimulationTimer) {
                window.clearInterval(metricSimulationTimer);
            }
            metricSimulationTimer = window.setInterval(() => {
                if (currentView !== 'student' || !liveMetricState.size) {
                    return;
                }
                tickStudentMetricState();
                renderStudentMetricCharts();
            }, 1000);
        }

        function setContentView(view) {
            currentView = view;
            const isStudentView = view === 'student';
            recognitionSection.style.display = isStudentView ? 'none' : '';
            studentDetailSection.classList.toggle('is-active', isStudentView);
            dashboardNav.classList.toggle('active', !isStudentView);
            studentExportCsvButton.disabled = !isStudentView || !liveMetricState.size;
            scheduleAttendanceStatusPoll();
        }

        function refreshOpenStudentDetail(person) {
            const trainingRecord = findTrainingRecord(person);
            const resolvedName = (trainingRecord && trainingRecord.name) || person.display_name || person.name || '學生';
            const resolvedStudentId = (trainingRecord && trainingRecord.student_id) || person.student_id || '尚未填寫學號';
            const presenceText = person.current_status === 'present' ? '在場中' : '已離開';
            const collegeText = (trainingRecord && trainingRecord.college) || person.college || '尚未設定';
            const departmentText = (trainingRecord && trainingRecord.department) || person.department || '尚未設定';
            const durationText = formatDuration(person.total_presence_time || 0);

            studentDetailName.textContent = resolvedName;
            studentDetailSubtitle.textContent = `${resolvedStudentId} 的個別頁面，整合即時出席分析、課堂圖表與學習歷程。`;
            studentSummaryName.textContent = resolvedName;
            studentSummaryStudentId.textContent = resolvedStudentId;
            studentSummaryCollege.textContent = collegeText;
            studentSummaryDepartment.textContent = departmentText;
            studentSummaryStatus.textContent = presenceText;
            studentSummaryDuration.textContent = durationText;
            studentDetailPresenceChart.innerHTML = buildSparkline(person.presence_points);

            return prepareStudentMetricState(selectedStudentId, person)
                .then(() => {
                    renderStudentMetricCharts();
                    studentExportCsvButton.disabled = false;
                });
        }

        function openStudentDetail(person) {
            selectedStudentId = person.user_id || person.student_id || studentSummaryStudentId.textContent.trim() || 'student';
            setContentView('student');
            studentExportCsvButton.disabled = true;
            refreshOpenStudentDetail(person)
                .then(() => {
                    startMetricSimulationLoop();
                    fetchAttendanceStatus();
                });
        }

        function refreshStreams() {
            const stamp = Date.now();
            colorImage.src = window.__URLS__.kinectColorFeed + '?t=' + stamp;
            depthImage.src = window.__URLS__.kinectDepthFeed + '?t=' + stamp;
        }

        function animateCapturedSlot(slot) {
            if (!slot) {
                return;
            }
            slot.classList.remove('just-captured');
            void slot.offsetWidth;
            slot.classList.add('just-captured');
        }

        function setCapturePending(enabled) {
            captureSlots.forEach((slot) => {
                slot.classList.remove('pending');
            });
            if (!enabled || currentEnrollCaptureCount >= captureSlots.length) {
                return;
            }
            captureSlots[currentEnrollCaptureCount].classList.add('pending');
        }

        function updateCaptureProgress(count) {
            const previousCount = currentEnrollCaptureCount;
            currentEnrollCaptureCount = count;
            captureCounter.textContent = `已拍攝 ${count} / 3`;
            captureSlots.forEach((slot, index) => {
                slot.classList.toggle('active', index < count);
                slot.classList.remove('pending');
            });
            if (count > previousCount) {
                for (let index = previousCount; index < count && index < captureSlots.length; index += 1) {
                    animateCapturedSlot(captureSlots[index]);
                }
            }
            captureFrameButton.disabled = count >= 3;
            captureFrameButton.textContent = count >= 3 ? '已拍滿 3 張' : '拍攝目前畫面';
            enrollSubmitButton.disabled = count < 3;
        }

        async function resetEnrollCaptureBuffer(tempId) {
            if (!tempId) {
                return;
            }

            try {
                await fetch(window.__URLS__.trainingCaptureReset, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ temp_id: tempId }),
                });
            } catch (error) {
                console.error('Failed to reset capture buffer', error);
            }
        }

        function setKinectButtonState(status) {
            toggleKinectButton.classList.remove('is-connected', 'is-disconnected', 'is-connecting');

            if (status === 'connected') {
                toggleKinectButton.textContent = 'Disconnect';
                toggleKinectButton.classList.add('is-connected');
                return;
            }

            if (status === 'connecting') {
                toggleKinectButton.textContent = '處理中...';
                toggleKinectButton.classList.add('is-connecting');
                return;
            }

            toggleKinectButton.textContent = 'Connect';
            toggleKinectButton.classList.add('is-disconnected');
        }

        function escapeHtml(value) {
            return String(value ?? '')
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;')
                .replaceAll('"', '&quot;')
                .replaceAll("'", '&#39;');
        }

        function formatDuration(seconds) {
            const safeSeconds = Math.max(0, Math.floor(Number(seconds || 0)));
            const minutes = Math.floor(safeSeconds / 60);
            const secs = safeSeconds % 60;
            if (minutes) {
                return `${minutes}m ${secs}s`;
            }
            return `${secs}s`;
        }

        function extractSequenceNumber(value) {
            const text = String(value || '').trim();
            if (!text) {
                return null;
            }
            const matches = text.match(/\d+/g);
            if (!matches || !matches.length) {
                return null;
            }
            const joined = matches.join('');
            const parsed = Number.parseInt(joined, 10);
            return Number.isFinite(parsed) ? parsed : null;
        }

        function compareBySequence(leftSource, rightSource) {
            const leftText = String(leftSource || '').trim();
            const rightText = String(rightSource || '').trim();
            const leftNumber = extractSequenceNumber(leftText);
            const rightNumber = extractSequenceNumber(rightText);

            if (leftNumber !== null && rightNumber !== null) {
                if (leftNumber !== rightNumber) {
                    return leftNumber - rightNumber;
                }
                return leftText.localeCompare(rightText, 'zh-Hant-u-co-stroke');
            }
            if (leftNumber !== null) {
                return -1;
            }
            if (rightNumber !== null) {
                return 1;
            }
            return leftText.localeCompare(rightText, 'zh-Hant-u-co-stroke');
        }

        function sortBySequence(items, sourceBuilder) {
            const cloned = Array.isArray(items) ? Array.from(items) : [];
            cloned.sort((left, right) => compareBySequence(sourceBuilder(left), sourceBuilder(right)));
            return cloned;
        }

        function getLatestConfirmedPeople() {
            return Array.isArray(window.__latestConfirmedPeople) ? window.__latestConfirmedPeople : [];
        }

        function buildStudentDetailSource(student) {
            const latestConfirmed = getLatestConfirmedPeople();
            const matchedConfirmed = latestConfirmed.find((person) => (
                (student.student_id && person.student_id === student.student_id)
                || (student.label && person.label === student.label)
                || (student.name && person.display_name === student.name)
            ));

            if (matchedConfirmed) {
                return matchedConfirmed;
            }

            return {
                user_id: student.student_id || student.label || student.name,
                label: student.label || student.name,
                display_name: student.name || student.label || '學生',
                name: student.name || student.label || '學生',
                student_id: student.student_id || '尚未填寫學號',
                college: student.college || '',
                department: student.department || '',
                current_status: 'absent',
                total_presence_time: 0,
                presence_points: [],
            };
        }

        function renderStudentSidebar(students) {
            studentSidebarList.innerHTML = '';

            if (!students || !students.length) {
                studentSidebarList.innerHTML = '<div class="empty-state" style="padding: 12px 14px; font-size: 0.84rem;">目前尚無學生資料</div>';
                return;
            }

            const orderedStudents = sortBySequence(
                students,
                (student) => `${student.student_id || ''} ${student.name || student.label || ''}`,
            );

            orderedStudents.forEach((student) => {
                const item = document.createElement('a');
                item.className = 'nav-item is-disabled';
                item.href = '#student-detail';
                item.dataset.studentLabel = student.label || '';
                item.innerHTML = `
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" stroke="currentColor" stroke-width="1.8"></path>
                        <path d="M5 20a7 7 0 0 1 14 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path>
                    </svg>
                    <div class="nav-copy">
                        <strong>${escapeHtml(student.name || student.label || '學生')}</strong>
                    </div>
                    <span class="nav-arrow">›</span>
                `;
                item.addEventListener('click', (event) => {
                    event.preventDefault();
                    openStudentDetail(buildStudentDetailSource(student));
                });
                studentSidebarList.appendChild(item);
            });
        }

        function updateTrainingRegistry(students) {
            trainingRegistry = new Map();
            (students || []).forEach((student) => {
                trainingRegistry.set(student.label, student);
            });
            renderStudentSidebar(Array.from(trainingRegistry.values()));
        }

        function buildStudentAvatar(name) {
            const safe = String(name || '?').trim();
            if (!safe) {
                return '?';
            }
            return safe.slice(0, 2).toUpperCase();
        }

        function formatChartTime(timestamp) {
            if (!timestamp) {
                return '--:--';
            }

            return new Date(timestamp * 1000).toLocaleTimeString('zh-TW', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
            });
        }

        function findTrainingRecord(person) {
            if (!person) {
                return null;
            }

            if (person.label && trainingRegistry.has(person.label)) {
                return trainingRegistry.get(person.label);
            }

            const normalizedStudentId = String(person.student_id || '').trim();
            const normalizedName = String(person.display_name || person.name || '').trim();

            for (const record of trainingRegistry.values()) {
                if (normalizedStudentId && String(record.student_id || '').trim() === normalizedStudentId) {
                    return record;
                }
                if (normalizedName && String(record.name || '').trim() === normalizedName) {
                    return record;
                }
            }

            return null;
        }

        function isEnrolledPerson(person) {
            const trainingRecord = findTrainingRecord(person);
            if (!trainingRecord) {
                return false;
            }

            const hasImages = Number(trainingRecord.image_count || 0) > 0;
            const hasIdentity = Boolean(String(person.student_id || trainingRecord.student_id || '').trim());
            return hasImages && hasIdentity;
        }

        function isPresentPerson(person) {
            return String(person?.current_status || '').trim().toLowerCase() === 'present';
        }

        function buildSparkline(points) {
            if (!points || !points.length) {
                return `
                    <div class="sparkline-shell">
                        <div class="sparkline-label">
                            <span>存在時間</span>
                            <span class="sparkline-live">更新中</span>
                        </div>
                        <div class="sparkline-placeholder">待身份確認後顯示</div>
                        <div class="sparkline-axis">
                            <span>--:--</span>
                            <span>--:--</span>
                            <span>--:--</span>
                        </div>
                    </div>
                `;
            }

            const width = 320;
            const height = 66;
            const paddingX = 8;
            const topY = 16;
            const bottomY = 54;
            const minTime = points[0].t;
            const maxTime = points[points.length - 1].t;
            const midTime = minTime + ((maxTime - minTime) / 2);
            const span = Math.max(1, maxTime - minTime);
            const x = (value) => paddingX + ((value - minTime) / span) * (width - paddingX * 2);
            const y = (value) => value ? topY : bottomY;
            const linePoints = points.map((point) => `${x(point.t).toFixed(1)},${y(point.v).toFixed(1)}`).join(' ');

            return `
                <div class="sparkline-shell">
                    <div class="sparkline-label">
                        <span>存在時間</span>
                        <span class="sparkline-live">更新中</span>
                    </div>
                    <svg class="presence-sparkline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
                        <line x1="${paddingX}" y1="${topY}" x2="${width - paddingX}" y2="${topY}" stroke="rgba(78,161,255,0.16)" stroke-width="1"></line>
                        <line x1="${paddingX}" y1="${bottomY}" x2="${width - paddingX}" y2="${bottomY}" stroke="rgba(122,142,182,0.22)" stroke-width="1"></line>
                        <polyline fill="none" stroke="#4ea1ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${linePoints}"></polyline>
                    </svg>
                    <div class="sparkline-axis">
                        <span>${formatChartTime(minTime)}</span>
                        <span>${formatChartTime(midTime)}</span>
                        <span>${formatChartTime(maxTime)}</span>
                    </div>
                </div>
            `;
        }

        function dedupeConfirmedPeople(confirmedPeople) {
            const merged = new Map();

            confirmedPeople.forEach((person) => {
                const trainingRecord = findTrainingRecord(person);
                const key = String(
                    (trainingRecord && trainingRecord.label)
                    || person.label
                    || (trainingRecord && trainingRecord.student_id)
                    || person.student_id
                    || person.user_id
                    || person.display_name
                    || ''
                ).trim().toLowerCase();

                if (!key) {
                    merged.set(`fallback-${merged.size}`, person);
                    return;
                }

                const current = merged.get(key);
                if (!current) {
                    merged.set(key, person);
                    return;
                }

                const currentScore = (current.current_status === 'present' ? 10000000000000 : 0) + Number(current.last_seen || 0);
                const nextScore = (person.current_status === 'present' ? 10000000000000 : 0) + Number(person.last_seen || 0);
                if (nextScore >= currentScore) {
                    merged.set(key, person);
                }
            });

            return Array.from(merged.values());
        }

        function renderStudentRows(temporaryPeople, confirmedPeople) {
            studentTrackList.innerHTML = '';
            const persistedConfirmedPeople = dedupeConfirmedPeople(confirmedPeople).filter((person) => {
                return isPresentPerson(person);
            });
            const orderedTemporaryPeople = sortBySequence(
                temporaryPeople,
                (person) => `${person.display_name || ''} ${person.temp_id || ''}`,
            );
            const orderedConfirmedPeople = sortBySequence(
                persistedConfirmedPeople,
                (person) => `${person.student_id || ''} ${person.display_name || person.name || person.user_id || ''}`,
            );

            if (!orderedTemporaryPeople.length && !orderedConfirmedPeople.length) {
                studentTrackList.innerHTML = '<div class="empty-state">開始課堂後，這裡會依人數產生學生列。</div>';
                return;
            }

            orderedTemporaryPeople.forEach((person) => {
                const isProcessing = person.confirm_status === 'processing';
                const statusText = person.confirm_message || (isProcessing ? '辨識中...' : '學號尚未確認');
                const row = document.createElement('article');
                row.className = 'student-line is-temporary';
                row.innerHTML = `
                    <div class="student-line-main">
                        <div class="student-line-avatar">${escapeHtml(buildStudentAvatar(person.display_name))}</div>
                        <div class="student-line-identity">
                            <strong>${escapeHtml(person.display_name)}</strong>
                            <span>${escapeHtml(statusText)}</span>
                        </div>
                    </div>
                    <div class="student-line-actions">
                        <button class="student-chip confirm" type="button" data-temp-id="${escapeHtml(person.temp_id)}" ${isProcessing ? 'disabled' : ''}>${isProcessing ? '辨識中...' : '確認身份'}</button>
                        <button class="student-chip enroll" type="button" data-enroll-temp-id="${escapeHtml(person.temp_id)}" data-enroll-display="${escapeHtml(person.display_name)}">加選</button>
                    </div>
                    <div class="student-line-chart">
                        ${buildSparkline([])}
                    </div>
                `;
                studentTrackList.appendChild(row);
            });

            orderedConfirmedPeople.forEach((person) => {
                const trainingRecord = findTrainingRecord(person);
                const isEnrolled = isEnrolledPerson(person);
                const resolvedName = (trainingRecord && trainingRecord.name) || person.display_name;
                const resolvedStudentId = (trainingRecord && trainingRecord.student_id) || person.student_id || '尚未填寫學號';
                const row = document.createElement('article');
                row.className = 'student-line is-clickable';
                row.dataset.studentId = person.user_id || person.student_id || resolvedStudentId;
                row.innerHTML = `
                    <div class="student-line-main">
                        <div class="student-line-avatar">${escapeHtml(buildStudentAvatar(resolvedName))}</div>
                        <div class="student-line-identity">
                            <strong>${escapeHtml(resolvedName)}</strong>
                            <span>${escapeHtml(resolvedStudentId)} · ${escapeHtml(person.current_status === 'present' ? '在場中' : '已離開')}</span>
                        </div>
                    </div>
                    <div class="student-line-actions">
                        <span class="student-chip ${isEnrolled ? 'enrolled' : 'absent'}">${isEnrolled ? '已加選' : '未加選'}</span>
                    </div>
                    <div class="student-line-chart">
                        ${buildSparkline(person.presence_points)}
                    </div>
                `;
                studentTrackList.appendChild(row);
            });
        }

        function applyAttendancePayload(payload) {
            setRecognitionMessage(payload.message || '課堂進行中。');
            statusFeedMessage.textContent = payload.announcement || payload.message || '班級狀態會在這裡顯示';
            const nextAttendanceMode = Boolean(payload.attendance_mode);
            attendanceMode = nextAttendanceMode;
            if (payload.current_course) {
                lastSyncedCourseKey = buildCourseSyncKey(
                    payload.current_course.course_id || '',
                    payload.current_course.course_name || '',
                );
                if (nextAttendanceMode || !selectedCourseName) {
                    setSelectedCourse(
                        payload.current_course.course_id || '',
                        payload.current_course.course_name || '',
                        false,
                    );
                }
            }
            if (!isAttendanceToggling) {
                attendanceButton.textContent = attendanceMode ? '結束課堂' : '開始課堂';
                attendanceButton.classList.toggle('active', attendanceMode);
            }

            if (payload.training_students) {
                updateTrainingRegistry(payload.training_students);
            }

            const temporaryPeople = attendanceMode ? (payload.temporary_people || []) : [];
            const confirmedPeople = attendanceMode ? (payload.confirmed_people || []) : [];
            window.__latestConfirmedPeople = confirmedPeople;
            const presentConfirmedPeople = confirmedPeople.filter(isPresentPerson);
            const presentConfirmedCount = presentConfirmedPeople.length;
            personCountPill.textContent = attendanceMode ? String(temporaryPeople.length + presentConfirmedCount) : '0';
            renderStudentRows(temporaryPeople, confirmedPeople);

            if (currentView === 'student' && selectedStudentId) {
                const selected = presentConfirmedPeople.find((person) => (person.user_id || person.student_id) === selectedStudentId);
                if (selected) {
                    refreshOpenStudentDetail(selected);
                } else {
                    setContentView('dashboard');
                }
            }
            syncAttendanceButtonAvailability();
        }

        const ATTENDANCE_STATUS_POLL_IDLE_MS = 1500;
        const ATTENDANCE_STATUS_POLL_DASHBOARD_MS = 1000;
        const ATTENDANCE_STATUS_POLL_STUDENT_MS = 850;
        let isAttendanceStatusFetching = false;
        let attendanceStatusPollTimer = 0;

        function getAttendanceStatusPollInterval() {
            if (!attendanceMode) {
                return ATTENDANCE_STATUS_POLL_IDLE_MS;
            }
            if (currentView === 'student' && selectedStudentId) {
                return ATTENDANCE_STATUS_POLL_STUDENT_MS;
            }
            return ATTENDANCE_STATUS_POLL_DASHBOARD_MS;
        }

        function scheduleAttendanceStatusPoll() {
            if (attendanceStatusPollTimer) {
                window.clearTimeout(attendanceStatusPollTimer);
            }
            attendanceStatusPollTimer = window.setTimeout(() => {
                fetchAttendanceStatus();
            }, getAttendanceStatusPollInterval());
        }

        async function fetchAttendanceStatus() {
            if (isAttendanceStatusFetching) {
                scheduleAttendanceStatusPoll();
                return;
            }
            isAttendanceStatusFetching = true;
            try {
                const query = new URLSearchParams();
                if (currentView === 'student' && selectedStudentId) {
                    query.set('include_metrics', '1');
                    query.set('metrics_user_id', selectedStudentId);
                } else {
                    query.set('include_metrics', '0');
                }
                const response = await fetch(window.__URLS__.attendanceStatus + "?${query.toString()}`);
                const payload = await response.json();
                applyAttendancePayload(payload);
            } catch (error) {
                setRecognitionMessage('無法取得課堂狀態。');
                statusFeedMessage.textContent = '請稍後再試。';
                personCountPill.textContent = '0';
                renderStudentRows([], []);
            } finally {
                isAttendanceStatusFetching = false;
                scheduleAttendanceStatusPoll();
            }
        }

        async function confirmTemporaryPerson(tempId, button) {
            const originalLabel = button.textContent;
            button.disabled = true;
            button.textContent = '辨識中...';

            try {
                const response = await fetch(window.__URLS__.confirmAttendancePerson, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ temp_id: tempId }),
                });
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.message || '身份確認失敗。');
                }
                setRecognitionMessage(payload.message || '身份確認已送出，背景辨識中。');
                statusFeedMessage.textContent = payload.message || statusFeedMessage.textContent;
                fetchAttendanceStatus();
            } catch (error) {
                button.disabled = false;
                button.textContent = originalLabel || '確認身份';
                setRecognitionMessage(error.message || '身份確認失敗。');
                statusFeedMessage.textContent = error.message || statusFeedMessage.textContent;
            }
        }

        function openEnrollModal(tempId, displayName) {
            enrollTempId.value = tempId;
            enrollName.value = displayName && !displayName.startsWith('學生') ? displayName : '';
            enrollStudentId.value = '';
            enrollCollege.value = '';
            enrollDepartment.value = '';
            updateCaptureProgress(0);
            enrollStatus.textContent = '先確認左側即時畫面，再手動拍滿 3 張照片。';
            enrollPreviewImage.src = window.__URLS__.kinectColorFeed + '?modal=' + Date.now();
            enrollModal.hidden = false;
            resetEnrollCaptureBuffer(tempId);
            setTimeout(() => {
                enrollName.focus();
            }, 0);
        }

        function closeEnrollModal() {
            resetEnrollCaptureBuffer(enrollTempId.value.trim());
            enrollModal.hidden = true;
            enrollForm.reset();
            enrollPreviewImage.src = '';
            updateCaptureProgress(0);
            enrollStatus.textContent = '先確認左側即時畫面，再手動拍滿 3 張照片。';
        }

        async function captureEnrollFrame() {
            const tempId = enrollTempId.value.trim();
            if (!tempId) {
                enrollStatus.textContent = '找不到目前要加選的暫時學生。';
                return;
            }

            captureFrameButton.disabled = true;
            captureFrameButton.textContent = '拍攝中...';
            setCapturePending(true);

            try {
                const response = await fetch(window.__URLS__.trainingCaptureFrame, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ temp_id: tempId }),
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.message || '拍攝失敗。');
                }

                updateCaptureProgress(Number(result.count || 0));
                enrollStatus.textContent = result.remaining > 0
                    ? `已拍攝 ${result.count}/3，還需要 ${result.remaining} 張。`
                    : '已拍滿 3 張照片，可以完成加選。';
            } catch (error) {
                setCapturePending(false);
                captureFrameButton.disabled = false;
                captureFrameButton.textContent = '拍攝目前畫面';
                enrollStatus.textContent = error.message || '拍攝失敗。';
            }
        }

        async function submitEnrollForm(event) {
            event.preventDefault();

            const payload = {
                temp_id: enrollTempId.value.trim(),
                name: enrollName.value.trim(),
                student_id: enrollStudentId.value.trim(),
                college: enrollCollege.value.trim(),
                department: enrollDepartment.value.trim(),
            };

            if (!payload.temp_id || !payload.name || !payload.student_id || !payload.college || !payload.department) {
                enrollStatus.textContent = '請先填好學生姓名、學號、院所、系所。';
                return;
            }
            if (currentEnrollCaptureCount < 3) {
                enrollStatus.textContent = '請先手動拍滿 3 張照片。';
                return;
            }

            enrollSubmitButton.disabled = true;
            enrollSubmitButton.textContent = '建立資料中...';

            try {
                const response = await fetch(window.__URLS__.trainingCapture, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.message || '加選失敗。');
                }

                if (result.students) {
                    updateTrainingRegistry(result.students);
                }
                if (result.attendance) {
                    applyAttendancePayload(result.attendance);
                } else {
                    fetchAttendanceStatus();
                }

                statusFeedMessage.textContent = result.message || statusFeedMessage.textContent;
                setRecognitionMessage(result.message || '已完成加選與 3 張訓練照片拍攝。');
                closeEnrollModal();
                refreshStreams();
            } catch (error) {
                enrollStatus.textContent = error.message || '加選失敗。';
            } finally {
                enrollSubmitButton.disabled = false;
                enrollSubmitButton.textContent = '完成加選';
                if (currentEnrollCaptureCount < 3) {
                    updateCaptureProgress(currentEnrollCaptureCount);
                }
            }
        }

        async function toggleKinect() {
            if (isKinectToggling) {
                return;
            }
            const isConnected = lastKinectStatus === 'connected';
            isKinectToggling = true;
            toggleKinectButton.disabled = true;
            toggleKinectButton.classList.remove('is-connected', 'is-disconnected');
            toggleKinectButton.classList.add('is-connecting');
            toggleKinectButton.textContent = isConnected ? '關閉中...' : '開啟中...';

            try {
                await fetch(
                    isConnected ? window.__URLS__.disconnectKinect : window.__URLS__.connectKinect,
                    { method: 'POST' },
                );
                refreshStreams();
            } catch (error) {
                setRecognitionMessage(isConnected ? 'Kinect 中斷失敗。' : 'Kinect 連線失敗。');
            } finally {
                setTimeout(() => {
                    isKinectToggling = false;
                    toggleKinectButton.disabled = false;
                    setKinectButtonState(lastKinectStatus === 'connected' ? 'connected' : 'disconnected');
                    syncAttendanceButtonAvailability();
                }, 500);
            }
        }

        function syncAttendanceButtonAvailability() {
            if (!attendanceButton) {
                return;
            }
            if (isAttendanceToggling) {
                attendanceButton.disabled = true;
                return;
            }
            if (attendanceMode) {
                attendanceButton.disabled = false;
                return;
            }
            if (lastKinectStatus !== 'connected') {
                attendanceButton.disabled = true;
                return;
            }
            attendanceButton.disabled = !selectedCourseName;
        }

        async function toggleAttendance() {
            if (isAttendanceToggling) {
                return;
            }
            if (!attendanceMode && !selectedCourseName) {
                const warningMessage = '請先選擇課程再開始課堂。';
                setRecognitionMessage(warningMessage);
                statusFeedMessage.textContent = warningMessage;
                if (courseSelect) {
                    courseSelect.focus();
                }
                return;
            }
            isAttendanceToggling = true;
            const previousAttendanceMode = attendanceMode;
            attendanceButton.disabled = true;
            attendanceButton.textContent = attendanceMode ? '關閉中...' : '開啟中...';
            if (!attendanceMode) {
                attendanceMode = true;
                attendanceButton.textContent = '結束課堂';
                attendanceButton.classList.add('active');
                setRecognitionMessage(`已開始課堂，課程：${selectedCourseName}`);
                statusFeedMessage.textContent = `已開始課堂，課程：${selectedCourseName}`;
                refreshStreams();
                syncAttendanceButtonAvailability();
            }

            try {
                let response;
                if (previousAttendanceMode) {
                    response = await fetch(window.__URLS__.stopAttendance, { method: 'POST' });
                } else {
                    response = await fetch(window.__URLS__.startAttendance, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            course_id: selectedCourseId,
                            course_name: selectedCourseName,
                        }),
                    });
                }
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.message || '課堂模式切換失敗。');
                }
                attendanceMode = Boolean(payload.attendance_mode);
                if (payload.current_course) {
                    setSelectedCourse(
                        payload.current_course.course_id || '',
                        payload.current_course.course_name || '',
                        false,
                    );
                }
                setRecognitionMessage(payload.message || recognitionStatus.textContent);
                statusFeedMessage.textContent = payload.message || statusFeedMessage.textContent;
                refreshStreams();
                fetchAttendanceStatus();
            } catch (error) {
                attendanceMode = previousAttendanceMode;
                setRecognitionMessage(error.message || '課堂模式切換失敗。');
            } finally {
                isAttendanceToggling = false;
                attendanceButton.textContent = attendanceMode ? '結束課堂' : '開始課堂';
                attendanceButton.classList.toggle('active', attendanceMode);
                syncAttendanceButtonAvailability();
            }
        }

        async function fetchKinectStatus() {
            try {
                const response = await fetch(window.__URLS__.kinectStatus);
                const payload = await response.json();

                if (lastKinectStatus !== payload.status) {
                    refreshStreams();
                    lastKinectStatus = payload.status;
                }

                if (payload.status === 'connected') {
                    if (!isKinectToggling) {
                        toggleKinectButton.disabled = false;
                        setKinectButtonState('connected');
                    }
                } else if (payload.status === 'disconnected') {
                    if (!isKinectToggling) {
                        toggleKinectButton.disabled = false;
                        setKinectButtonState('disconnected');
                    }
                } else {
                    if (!isKinectToggling) {
                        toggleKinectButton.disabled = true;
                        setKinectButtonState('connecting');
                    }
                }
                syncAttendanceButtonAvailability();
            } catch (error) {
                if (!isKinectToggling) {
                    toggleKinectButton.disabled = false;
                    setKinectButtonState('disconnected');
                }
                syncAttendanceButtonAvailability();
            }
        }

        toggleKinectButton.addEventListener('click', toggleKinect);
        attendanceButton.addEventListener('click', toggleAttendance);
        updateTrainingRegistry(Array.isArray(initialTrainingStudents) ? initialTrainingStudents : []);
        studentTrackList.addEventListener('click', (event) => {
            const confirmButton = event.target.closest('[data-temp-id]');
            if (confirmButton) {
                confirmTemporaryPerson(confirmButton.dataset.tempId, confirmButton);
                return;
            }

            const enrollButton = event.target.closest('[data-enroll-temp-id]');
            if (enrollButton) {
                openEnrollModal(enrollButton.dataset.enrollTempId, enrollButton.dataset.enrollDisplay || '');
                return;
            }

            const studentRow = event.target.closest('.student-line.is-clickable');
            if (studentRow) {
                const confirmedPeople = attendanceMode ? (window.__latestConfirmedPeople || []).filter(isPresentPerson) : [];
                const selected = confirmedPeople.find((person) => (person.user_id || person.student_id || '') === studentRow.dataset.studentId);
                if (selected) {
                    openStudentDetail(selected);
                }
            }
        });
        dashboardNav.addEventListener('click', (event) => {
            event.preventDefault();
            setContentView('dashboard');
        });
        studentDetailBackButton.addEventListener('click', () => {
            setContentView('dashboard');
        });
        if (themeToggleButton) {
            themeToggleButton.addEventListener('click', () => {
                const currentTheme = normalizeDashboardTheme(document.documentElement.getAttribute('data-dashboard-theme') || 'light');
                setDashboardTheme(currentTheme === 'dark' ? 'light' : 'dark');
            });
        }
        if (profileMenu && profileMenuButton) {
            profileMenuButton.addEventListener('click', (event) => {
                const clickedNode = event.target instanceof Element ? event.target : null;
                const markClicked = clickedNode ? clickedNode.closest('.brand-mark') : null;
                const keyboardTriggered = event.detail === 0;
                if (!markClicked && !keyboardTriggered) {
                    return;
                }
                event.stopPropagation();
                clearProfileMenuCloseTimer();
                setProfileMenuOpen(!profileMenu.classList.contains('is-open'));
            });
            if (profileMark) {
                profileMark.addEventListener('mouseenter', () => {
                    clearProfileMenuCloseTimer();
                    profileMenu.classList.add('is-hover-mark');
                    setProfileMenuOpen(true);
                });
                profileMark.addEventListener('mouseleave', () => {
                    scheduleProfileMenuClose();
                });
            }
            if (profilePanel) {
                profilePanel.addEventListener('mouseenter', () => {
                    clearProfileMenuCloseTimer();
                });
                profilePanel.addEventListener('mouseleave', () => {
                    profileMenu.classList.remove('is-hover-mark');
                    scheduleProfileMenuClose();
                });
            }
            if (profileAlertAnchor && alertBellButton && alertPanel) {
                alertBellButton.addEventListener('click', (event) => {
                    event.stopPropagation();
                    setAlertPanelOpen(!profileAlertAnchor.classList.contains('is-open'));
                });
                profileAlertAnchor.addEventListener('click', (event) => {
                    event.stopPropagation();
                });
            }
            profileMenu.addEventListener('click', (event) => {
                event.stopPropagation();
            });
            document.addEventListener('click', () => {
                clearProfileMenuCloseTimer();
                setProfileMenuOpen(false);
            });
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    clearProfileMenuCloseTimer();
                    setProfileMenuOpen(false);
                }
            });
        }
        if (teacherChatWidget && teacherChatToggle) {
            teacherChatToggle.addEventListener('click', (event) => {
                event.stopPropagation();
                const nextOpen = !teacherChatWidget.classList.contains('is-open');
                setTeacherChatOpen(nextOpen, { focusInput: nextOpen });
            });
            if (teacherChatPanel) {
                teacherChatPanel.addEventListener('click', (event) => {
                    event.stopPropagation();
                });
            }
            if (teacherChatClose) {
                teacherChatClose.addEventListener('click', () => {
                    setTeacherChatOpen(false);
                });
            }
            if (teacherChatSend) {
                teacherChatSend.addEventListener('click', submitTeacherChatMessage);
            }
            if (teacherChatInput) {
                teacherChatInput.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter') {
                        event.preventDefault();
                        submitTeacherChatMessage();
                    }
                });
            }
            document.addEventListener('click', (event) => {
                if (!teacherChatWidget.contains(event.target)) {
                    setTeacherChatOpen(false);
                }
            });
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    setTeacherChatOpen(false);
                }
            });
        }
        studentExportCsvButton.addEventListener('click', handleStudentExportCsv);
        enrollForm.addEventListener('submit', submitEnrollForm);
        captureFrameButton.addEventListener('click', captureEnrollFrame);
        enrollCloseButton.addEventListener('click', closeEnrollModal);
        enrollCancelButton.addEventListener('click', closeEnrollModal);
        enrollModal.addEventListener('click', (event) => {
            if (event.target === enrollModal) {
                closeEnrollModal();
            }
        });
        initializeDashboardTheme();
        initializeCoursePicker();
        updateCaptureProgress(0);
        setTeacherChatOpen(false);
        window.__latestConfirmedPeople = [];
        setContentView('dashboard');
        fetchAttendanceStatus();
        fetchKinectStatus();
        setInterval(fetchKinectStatus, 1500);
