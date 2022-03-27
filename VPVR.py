##https://cn.tradingview.com/support/solutions/43000502040/

class VPVR:
    def __init__(self,value_area_pct):
        self.value_area_pct = value_area_pct
    def midmax_idx(self,array):
        if len(array) == 0:
            return None

        # Find candidate maxima
        maxima_idxs = np.argwhere(array == np.amax(array))[:,0]
        if len(maxima_idxs) == 1:
            return maxima_idxs[0]
        elif len(maxima_idxs) <= 1:
            return None

        # Find the distances from the midpoint to find
        # the maxima with the least distance
        midpoint = len(array) / 2
        v_norm = np.vectorize(np.linalg.norm)
        maximum_idx = np.argmin(v_norm(maxima_idxs - midpoint))

        return maxima_idxs[maximum_idx]
    
    def calculate_value_area(self):
        target_vol = self.total_volume * self.value_area_pct
        trial_vol = self.poc_volume 

        min_idx = self.poc_idx
        max_idx = self.poc_idx

        while trial_vol <= target_vol:
            last_min = min_idx
            last_max = max_idx
            
            next_min_idx = np.clip(min_idx - 1, 0, len(self.profile) - 1)
            next_max_idx = np.clip(max_idx + 1, 0, len(self.profile) - 1)

            low_volume = self.profile.iloc[next_min_idx] if next_min_idx != last_min else None
            high_volume = self.profile.iloc[next_max_idx] if next_max_idx != last_max else None

            if not high_volume or (low_volume and low_volume > high_volume):
                trial_vol += low_volume
                min_idx = next_min_idx
            elif not low_volume or (high_volume and low_volume <= high_volume):
                trial_vol += high_volume
                max_idx = next_max_idx
            else:
                break

        return self.profile.index[min_idx], self.profile.index[max_idx]
    
    def vpvr_indicator(self,df):
        self.profile = df.groupby("close")["volume"].sum()
        self.total_volume = self.profile.sum()
        self.profile_range = self.profile.index.min(), self.profile.index.max()
        self.poc_idx = self.midmax_idx(self.profile.values.tolist())
        if self.poc_idx is not None:
            self.poc_volume = self.profile.iloc[self.poc_idx]
            self.poc_price = self.profile.index[self.poc_idx]
            self.value_area = self.calculate_value_area()
        else:
            self.poc_volume = None
            self.poc_price = None
            self.value_area = [None, None]
        return self.poc_price,self.value_area[0],self.value_area[1]
    
def vpvr(datafeed,value_area_pct):
    '''
    V,C,H,L
    '''
    #1.find maxvol and poc 
    max_vol_idx = np.argmax(datafeed.volume)
    max_vol = datafeed.volume[max_vol_idx]
    max_vol_POC = datafeed.close[max_vol_idx]
    total_volume = np.sum(datafeed.volume)
    target_volume = total_volume*value_area_pct 

    ##samll to large 
    close_sorted_index = np.argsort(datafeed.close)
    poc_index_after_sorted = np.argwhere(close_sorted_index == max_vol_idx).flatten()[0]
    trial_vol = max_vol
    min_idx = poc_index_after_sorted
    max_idx = poc_index_after_sorted 
    ###以 close排序后的poc为中心向两端扩展 
    while trial_vol <=target_volume:
        next_min_idx = np.clip(min_idx-1,0,len(close_sorted_index)-1)
        next_max_idx = np.clip(max_idx+1,0,len(close_sorted_index)-1)
        low_volume = datafeed.volume[close_sorted_index[next_min_idx]] if next_min_idx != min_idx else None 
        high_volume = datafeed.volume[close_sorted_index[next_max_idx]] if next_max_idx !=max_idx else None 

        if not high_volume or (low_volume and low_volume > high_volume):
            trial_vol += low_volume 
            min_idx = next_min_idx 
        elif not low_volume or (high_volume and low_volume <=high_volume):
            trial_vol += high_volume
            max_idx = next_max_idx
        else:
            break
    
    return datafeed.close[max_vol_idx],datafeed.close[close_sorted_index[min_idx]],datafeed.close[close_sorted_index[max_idx]]



