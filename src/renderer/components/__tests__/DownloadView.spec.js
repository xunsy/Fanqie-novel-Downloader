import { shallowMount } from '@vue/test-utils';
import DownloadView from '../DownloadView.vue';

// Mock the global window.electron object
global.window = {
  electron: {
    downloadNovel: jest.fn(),
    onDownloadProgress: jest.fn(),
    onDownloadComplete: jest.fn(),
  },
};

describe('DownloadView.vue', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallowMount(DownloadView);
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  it('renders the initial component correctly', () => {
    expect(wrapper.find('h1').text()).toBe('下载小说');
    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
    expect(wrapper.find('button').text()).toBe('下载');
  });

  it('calls downloadNovel when the download button is clicked with a valid novel ID', async () => {
    const input = wrapper.find('input[type="text"]');
    await input.setValue('12345');
    
    const downloadButton = wrapper.find('button');
    await downloadButton.trigger('click');

    expect(window.electron.downloadNovel).toHaveBeenCalledWith('12345');
  });

  it('does not call downloadNovel when the novel ID is empty', async () => {
    const downloadButton = wrapper.find('button');
    await downloadButton.trigger('click');

    expect(window.electron.downloadNovel).not.toHaveBeenCalled();
  });

  it('updates progress when onDownloadProgress event is received', async () => {
    // Simulate receiving a progress update
    const progress = {
      total: 100,
      current: 25,
      message: 'Downloading chapter 25/100',
    };
    // Manually call the handler that would be set up in mounted
    wrapper.vm.handleDownloadProgress(null, progress);
    
    await wrapper.vm.$nextTick();
    
    expect(wrapper.vm.progress).toBe(25);
    expect(wrapper.vm.progressMessage).toBe('Downloading chapter 25/100');
    expect(wrapper.find('.progress-bar').exists()).toBe(true);
    expect(wrapper.find('.progress-bar').attributes('style')).toContain('width: 25%;');
  });

  it('updates status to success on download complete', async () => {
    // Simulate a successful download
    const result = {
      success: true,
      message: '下载完成',
    };
    wrapper.vm.handleDownloadComplete(null, result);

    await wrapper.vm.$nextTick();

    expect(wrapper.vm.downloadStatus).toBe('success');
    expect(wrapper.vm.statusMessage).toBe('下载完成');
  });

  it('updates status to error on download failure', async () => {
    // Simulate a failed download
    const result = {
      success: false,
      message: '下载失败',
    };
    wrapper.vm.handleDownloadComplete(null, result);

    await wrapper.vm.$nextTick();

    expect(wrapper.vm.downloadStatus).toBe('error');
    expect(wrapper.vm.statusMessage).toBe('下载失败');
  });
});