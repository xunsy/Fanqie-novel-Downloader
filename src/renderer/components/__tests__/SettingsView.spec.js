import { shallowMount } from '@vue/test-utils';
import SettingsView from '../SettingsView.vue';

// Mock the global window.electron object
const mockSettings = {
  savePath: '/mock/path',
  concurrentDownloads: 5,
};

global.window = {
  electron: {
    getSettings: jest.fn().mockResolvedValue(mockSettings),
    saveSettings: jest.fn().mockResolvedValue({ success: true }),
    selectDirectory: jest.fn().mockResolvedValue('/new/selected/path'),
  },
};

describe('SettingsView.vue', () => {
  let wrapper;

  beforeEach(async () => {
    wrapper = shallowMount(SettingsView);
    // Wait for the component to finish its async created hook
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the component and loads initial settings', () => {
    expect(wrapper.find('h1').text()).toBe('设置');
    expect(window.electron.getSettings).toHaveBeenCalled();
    expect(wrapper.vm.settings.savePath).toBe('/mock/path');
    expect(wrapper.find('input#savePath').element.value).toBe('/mock/path');
    expect(wrapper.find('input#concurrentDownloads').element.value).toBe('5');
  });

  it('allows the user to select a new directory', async () => {
    const selectDirButton = wrapper.find('button.select-dir');
    await selectDirButton.trigger('click');
    expect(window.electron.selectDirectory).toHaveBeenCalled();
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.settings.savePath).toBe('/new/selected/path');
  });

  it('saves the settings when the form is submitted', async () => {
    // Modify the settings
    const savePathInput = wrapper.find('input#savePath');
    await savePathInput.setValue('/new/path');
    const concurrentDownloadsInput = wrapper.find('input#concurrentDownloads');
    await concurrentDownloadsInput.setValue('10');

    // Submit the form
    const form = wrapper.find('form');
    await form.trigger('submit.prevent');
    
    await wrapper.vm.$nextTick();

    // Check that saveSettings was called with the new values
    expect(window.electron.saveSettings).toHaveBeenCalledWith({
      savePath: '/new/path',
      concurrentDownloads: 10,
    });
    
    // Check for success message
    expect(wrapper.find('.status-message.success').exists()).toBe(true);
    expect(wrapper.find('.status-message.success').text()).toBe('设置已保存！');
  });

  it('shows an error message if saving fails', async () => {
    // Mock a failed save
    window.electron.saveSettings.mockResolvedValueOnce({ success: false, message: '保存失败' });

    const form = wrapper.find('form');
    await form.trigger('submit.prevent');

    await wrapper.vm.$nextTick();

    expect(window.electron.saveSettings).toHaveBeenCalled();
    expect(wrapper.find('.status-message.error').exists()).toBe(true);
    expect(wrapper.find('.status-message.error').text()).toBe('保存失败');
  });
});