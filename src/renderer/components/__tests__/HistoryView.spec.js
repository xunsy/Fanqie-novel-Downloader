import { shallowMount } from '@vue/test-utils';
import HistoryView from '../HistoryView.vue';

// Mock the global window.electron object
const mockHistory = [
  { id: '1', novelId: '1001', title: '小说1', downloadedAt: new Date().toISOString() },
  { id: '2', novelId: '1002', title: '小说2', downloadedAt: new Date().toISOString() },
];

global.window = {
  electron: {
    getHistory: jest.fn().mockResolvedValue(mockHistory),
    clearHistory: jest.fn().mockResolvedValue({ success: true }),
    downloadNovel: jest.fn(),
  },
};

describe('HistoryView.vue', () => {
  let wrapper;

  beforeEach(async () => {
    wrapper = shallowMount(HistoryView);
    // Wait for the component to finish its async created hook
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the component and loads history', () => {
    expect(wrapper.find('h1').text()).toBe('下载历史');
    expect(window.electron.getHistory).toHaveBeenCalled();
    expect(wrapper.findAll('tbody tr').length).toBe(2);
    expect(wrapper.text()).toContain('小说1');
    expect(wrapper.text()).toContain('小说2');
  });

  it('calls downloadNovel when a "Redownload" button is clicked', async () => {
    const redownloadButton = wrapper.find('tbody tr:first-child .redownload-btn');
    await redownloadButton.trigger('click');
    expect(window.electron.downloadNovel).toHaveBeenCalledWith('1001');
  });

  it('clears the history when the "Clear History" button is clicked', async () => {
    const clearButton = wrapper.find('button.clear-history-btn');
    await clearButton.trigger('click');

    expect(window.electron.clearHistory).toHaveBeenCalled();
    
    // Simulate the history being cleared after the call
    window.electron.getHistory.mockResolvedValueOnce([]);
    // Manually trigger a refresh
    await wrapper.vm.loadHistory();
    await wrapper.vm.$nextTick();

    expect(wrapper.findAll('tbody tr').length).toBe(0);
  });
  
  it('displays a message when history is empty', async () => {
    // Mount a new component with empty history
    window.electron.getHistory.mockResolvedValueOnce([]);
    const emptyWrapper = shallowMount(HistoryView);
    await emptyWrapper.vm.$nextTick();
    await emptyWrapper.vm.$nextTick();
    
    expect(emptyWrapper.find('p').text()).toBe('没有下载历史。');
    expect(emptyWrapper.find('table').exists()).toBe(false);
  });
});