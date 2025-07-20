import { shallowMount } from '@vue/test-utils';
import AboutView from '../AboutView.vue';

// Mock the global window.electron object
global.window = {
  electron: {
    getVersion: jest.fn(() => '1.0.0-test'),
  },
};

describe('AboutView.vue', () => {
  it('renders the version number from window.electron', async () => {
    const wrapper = shallowMount(AboutView);
    // Wait for next tick to allow component to update
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('Version: 1.0.0-test');
    expect(window.electron.getVersion).toHaveBeenCalled();
  });

  it('renders the component correctly', () => {
    const wrapper = shallowMount(AboutView);
    expect(wrapper.find('h1').text()).toBe('关于');
    expect(wrapper.find('p').text()).toContain('Tomato Novel Downloader');
  });
});