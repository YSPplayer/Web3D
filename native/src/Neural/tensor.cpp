 #include "tensor.h"
#include <opencv2/opencv.hpp>
#include <utility>
#include "../log.h"
#include "sample.h"
#include <limits>
/*
rows = h
cols = w
*/
namespace DeepLr::Neural {
	std::random_device Tensor3D::rd;
	std::mt19937 Tensor3D::gen(rd());
	Tensor3D::Tensor3D():c(1),w(NEURAL_W),h(NEURAL_H),data(1 * NEURAL_W * NEURAL_H,0.0f) {}
	Tensor3D::Tensor3D(int32_t c, int32_t w, int32_t h){
		this->c = c;
		this->w = w;
		this->h = h;
		this->data = std::vector(c * w * h, 0.0f);
	}
	Tensor3D::Tensor3D(const Tensor3D& tensor3D) {
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = tensor3D.data;
	}
	Tensor3D::Tensor3D(Tensor3D&& tensor3D) {
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = std::move(tensor3D.data);
	}

	Tensor3D& Tensor3D::operator=(const Tensor3D& tensor3D) {
		if (this == &tensor3D) {
			return *this;
		}
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = tensor3D.data;
		return *this;
	}

	Tensor3D& Tensor3D::operator=(Tensor3D&& tensor3D) noexcept {
		if (this == &tensor3D) {
			return *this;
		}
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = std::move(tensor3D.data);
		return *this;
	}
	Tensor3D Tensor3D::operator*(float other) {
		Tensor3D result = *this;
		std::transform(result.data.begin(), result.data.end(), result.data.begin(),
			[other](float x) { return x * other; });
		return result;
	}
	Tensor3D Tensor3D::operator*(const Tensor3D& other) {
		if (Channel() != 1 || other.Channel() != 1) {
			throw std::invalid_argument("Matrix dimension error: dimension is not 1");
		}
		if (this->w != other.h) {
			throw std::invalid_argument(std::format("Matrix dimension error: Dimensions cannot be multiplied.a shape:{},b shape:{} ",
				this->w, other.h));
		}
		Tensor3D tensor3D(1, other.w ,this->h);
		for (int32_t y = 0; y < tensor3D.h; ++y) {
			for (int32_t x = 0; x < tensor3D.w; ++x) {
				float sum = 0;
				for (int32_t k = 0; k < this->w; ++k) {
					sum += this->At(0, y, k) * other.At(0,k, x);
				}
				tensor3D.At(0, y, x) = sum;
			}
		}
		return tensor3D;
	}

	Tensor3D Tensor3D::operator+(const Tensor3D& other) {
		if (Channel() != other.Channel()) {
			throw std::invalid_argument("Matrix dimension error: dimension is not 1");
		}
		if (this->w != other.w || this->h != other.h) {
			throw std::invalid_argument(std::format("Matrix dimension error: Dimensions cannot be multiplied.a shape:{} * {},b shape:{} * {} ",
				this->w, this->h, other.w, other.h));
		}
		Tensor3D tensor3D(other.c, other.w, other.h);
		for (int32_t c = 0; c < tensor3D.c; ++c) {
			for (int32_t y = 0; y < tensor3D.h; ++y) {
				for (int32_t x = 0; x < tensor3D.w; ++x) {
					tensor3D.At(c, y, x) = this->Get(c, y, x) + other.Get(c, y, x);
				}
			}
		}
		return tensor3D;
	}

	Tensor3D Tensor3D::operator-(const Tensor3D& other) {
		if (Channel() != other.Channel()) {
			throw std::invalid_argument("Matrix dimension error: dimension is not 1");
		}
		if (this->w != other.w || this->h != other.h) {
			throw std::invalid_argument(std::format("Matrix dimension error: Dimensions cannot be multiplied.a shape:{} * {},b shape:{} * {} ",
				this->w, this->h, other.w, other.h));
		}
		Tensor3D tensor3D(other.c, other.w, other.h);
		for (int32_t c = 0; c < tensor3D.c; ++c) {
			for (int32_t y = 0; y < tensor3D.h; ++y) {
				for (int32_t x = 0; x < tensor3D.w; ++x) {
					tensor3D.At(c, y, x) = this->Get(c, y, x) - other.Get(c, y, x);
				}
			}
		}
		return tensor3D;
	}

	float Tensor3D::Min() const {
		float result = std::numeric_limits<float>::max();
		for (int32_t i = 0; i < Count(); ++i) {
			result = std::min(result, Get(i));
		}
		return result;
	}

	float Tensor3D::Max() const {
		float result = std::numeric_limits<float>::lowest();
		for (int32_t i = 0; i < Count(); ++i) {
			result = std::max(result, Get(i));
		}
		return result;
	}

	float Tensor3D::SumAbs() const {
		float sum = 0.0f;
		for (int32_t i = 0; i < Count(); ++i) {
			sum += std::fabs(Get(i));
		}
		return sum;
	}

	float Tensor3D::SumAbs(const std::vector<Tensor3D>& tensors) {
		float sum = 0.0f;
		for (const Tensor3D& tensor : tensors) {
			sum += tensor.SumAbs();
		}
		return sum;
	}
	float Tensor3D::TargetProbMean(const std::array<int32_t, 4>& target) const {
		float sum = 0.0f;
		for (int32_t i = 0; i < target.size(); ++i) {
			sum += Get(0, i, target[i]);
		}
		return sum / (float)target.size();
	}
	std::vector<float> Tensor3D::GetW(int32_t y) const {
		if(c != 1) return std::vector<float>();
		std::vector<float> result;
		result.resize(w);
		for (int32_t x = 0; x < w; ++x) {
			result[x] = Get(0, y, x);
		}
		return result;
	}

	std::vector<float> Tensor3D::GetH(int32_t x) const {
		if (c != 1) return std::vector<float>();
		std::vector<float> result;
		result.resize(h);
		for (int32_t y = 0; y < h; ++y) {
			result[y] = Get(0, y, x);
		}
		return result;
	}
	/// <summary>
	/// Ëæ»ú³õÊ¼»¯
	/// </summary>
	void Tensor3D::HeUniform(int32_t shape) {
		float limit = std::sqrt(6.0f / (float)shape);
		std::uniform_real_distribution<float> dist(-limit, limit);
		for (int32_t i = 0; i < Shape(); ++i) {
			At(i) = dist(gen);
		}
	}
	bool Tensor3D::Transpose() {
		if (c != 1) {
			return false;
		}
		int32_t oldW = w;
		int32_t oldH = h;
		std::vector<float> newData(oldW * oldH);
		for (int32_t y = 0; y < oldH; ++y) {
			for (int32_t x = 0; x < oldW; ++x) {
				int32_t oldIndex = y * oldW + x;
				int32_t newY = x;
				int32_t newX = y;
				int32_t newW = oldH;
				int32_t newIndex = newY * newW + newX;
				newData[newIndex] = data[oldIndex];
			}
		}
		data = std::move(newData);
		w = oldH;
		h = oldW;
		return true;
	}

	bool Tensor3D::ReShape(int32_t c, int32_t w, int32_t h) {
		if (this->c * this->w * this->h == c * w * h) {
			this->c = c;
			this->w = w;
			this->h = h;
			return true;
		}
		return false;
	}

	Tensor3D Tensor3D::Load(const std::string& path) {
		cv::Mat img = cv::imread(path, cv::IMREAD_GRAYSCALE);
		Tensor3D tensor3D;
		if (img.empty()) {
			Log::Debug("Failed to read image:" + path);
			return tensor3D;
		}
		if (img.cols != NEURAL_W || img.rows != NEURAL_H) {
			Log::Debug(std::format("current size:{}:{},Activate forced scaling.", img.cols, img.rows));
			cv::resize(img, img, cv::Size(128, 128), 0, 0, cv::INTER_LINEAR);
		}
		for (int32_t y = 0; y < NEURAL_H; ++y) {
			const uchar* row = img.ptr<uchar>(y);
			for (int32_t x = 0; x < 128; ++x) {
				tensor3D.At(0, y, x) = row[x] / 255.0f;
			}
		}
		return tensor3D;
		
	}
}